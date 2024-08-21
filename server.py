import grpc
import asyncio
from concurrent import futures
import reverse_shell_pb2
import reverse_shell_pb2_grpc

class ReverseShellService(reverse_shell_pb2_grpc.ReverseShellServiceServicer):
    async def StartSession(self, request_iterator, context):
        # Send the static command once and then end the stream
        command = 'top'
        print(f"Sending Static Command: {command}")
        yield reverse_shell_pb2.CommandResponse(output=f"{command}", is_active=True)
        
        # End of command sending
        await asyncio.sleep(1)  # Ensure the client gets a chance to process the command
        yield reverse_shell_pb2.CommandResponse(output="Command finished\n", is_active=False)

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    reverse_shell_pb2_grpc.add_ReverseShellServiceServicer_to_server(ReverseShellService(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
