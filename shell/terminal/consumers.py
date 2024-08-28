import json
import asyncio
import grpc
import terminal.reverse_shell_pb2 as reverse_shell_pb2
import terminal.reverse_shell_pb2_grpc as reverse_shell_pb2_grpc
import time
from channels.generic.websocket import AsyncWebsocketConsumer
import re

ANSI_ESCAPE = re.compile(r'\x1b\[([0-9;]*)m')

def remove_ansi_escape_sequences(text):
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub('', text)

class CommandAndStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command', '')

        if command:
            request_id = f"command-{hash(command + str(time.time()))}"
            await self.add_command_to_grpc(command, request_id)

            async for chunk in self.async_event_stream(request_id):
                # Ensure each chunk is separated by a newline character
                formatted_chunk = remove_ansi_escape_sequences(chunk)
                await self.send(text_data=json.dumps({"output": formatted_chunk}))

    async def add_command_to_grpc(self, command, request_id):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
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
