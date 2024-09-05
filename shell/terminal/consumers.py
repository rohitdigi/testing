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

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command', '')

        if command:
            request_id = f"command-{hash(command + str(time.time()))}"
            self.command_queue.append((command, request_id))
            if not self.processing_command or command == "stop":
                await self.process_commands()

    async def process_commands(self):
        self.processing_command = True
        while self.command_queue:
            command, request_id = self.command_queue.popleft()

            # # Handle "stop" command immediately if received
            # if command == "stop":
            #     logging.info("--------------------Got the stop command------------------>")
            #     await self.send_stop_signal()
            #     break  # Break out of the loop to prioritize "stop"

            self.current_request_id = request_id
            await self.add_command_to_grpc(command, request_id)

            if command != "stop":
                async for chunk in self.async_event_stream(request_id):
                    formatted_chunk = remove_ansi_escape_sequences(chunk)
                    await self.send(text_data=json.dumps({"output": formatted_chunk}))

        self.processing_command = False

    async def add_command_to_grpc(self, command, request_id):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            logging.info("--------------------INSIDE-ADDCOMMAND------------------>")
            stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)
            command_request = reverse_shell_pb2.CommandRequest(request_id=request_id, command=command)
            await stub.AddCommand(command_request)

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

    # async def send_stop_signal(self):
    #     if self.current_request_id:
    #         # Sending stop command to the gRPC server for the ongoing process
    #         async with grpc.aio.insecure_channel('localhost:50051') as channel:
    #             stub = reverse_shell_pb2_grpc.ReverseShellServiceStub(channel)
    #             stop_request = reverse_shell_pb2.CommandRequest(request_id=self.current_request_id, command="stop")
    #             await stub.AddCommand(stop_request)
    #         await self.send(text_data=json.dumps({"output": "Process interrupted by stop command."}))
