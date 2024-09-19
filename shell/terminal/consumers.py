import json
import asyncio
import grpc
import terminal.reverse_shell_pb2 as reverse_shell_pb2
import terminal.reverse_shell_pb2_grpc as reverse_shell_pb2_grpc
import time
from channels.generic.websocket import AsyncWebsocketConsumer
import re
import logging
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# ANSI escape sequence regex pattern
ANSI_ESCAPE = re.compile(r'''
    \x1b   # ESC
    (?:    # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |      # or [ for CSI
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
    |      # Match specific (B characters
    \(B
''', re.VERBOSE)

def remove_ansi_escape_sequences(text):
    return ANSI_ESCAPE.sub('', text)

class CommandAndStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_queue = deque()
        self.processing_command = False
        self.current_request_id = None
        self.mac_address = None  # To be set based on user input or session

    async def connect(self):
        await self.accept()
        logger.info("WebSocket connection accepted.")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command', '')
        self.mac_address = data.get('mac_address', '2C:54:91:88:C9:E3')  # Expecting MAC address from client

        if command and self.mac_address:
            request_id = f"command-{hash(command + str(time.time()))}"
            self.command_queue.append((command, request_id, self.mac_address))
            logger.info(f"Received command: {command} for MAC address: {self.mac_address}")

            if not self.processing_command:
                await self.process_commands()
        else:
            await self.send(text_data=json.dumps({"error": "Command or MAC address not provided."}))

    async def process_commands(self):
        self.processing_command = True
        while self.command_queue:
            command, request_id, mac_address = self.command_queue.popleft()

            # Add command to gRPC server
            self.current_request_id = request_id
            await self.add_command_to_grpc(command, request_id, mac_address)

            # Fetch and send the response
            if command != "stop":
                async for chunk in self.async_event_stream(request_id):
                    formatted_chunk = remove_ansi_escape_sequences(chunk)
                    await self.send(text_data=json.dumps({"output": formatted_chunk}))
        self.processing_command = False

    async def add_command_to_grpc(self, command, request_id, mac_address):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)
            command_request = reverse_shell_pb2.CommandRequest(
                request_id=request_id,
                command=command,
                macAddress=mac_address
            )
            await stub.AddCommand(command_request)
            logger.info(f"Command '{command}' sent to gRPC server for MAC address {mac_address} with Request ID {request_id}.")

    async def async_event_stream(self, request_id):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)
            request = reverse_shell_pb2.RequestID(request_id=request_id)
            async for response in stub.GetResponse(request):
                output = remove_ansi_escape_sequences(response.output)
                if output:
                    yield output  # Output already contains newlines
                if not response.is_active:
                    break

