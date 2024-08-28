# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import terminal.reverse_shell_pb2 as reverse__shell__pb2

GRPC_GENERATED_VERSION = '1.65.5'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.66.0'
SCHEDULED_RELEASE_DATE = 'August 6, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in reverse_shell_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class ReverseShellServiceStub(object):
    """The ReverseShellService definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.StartSession = channel.stream_stream(
                '/reverse_shell.ReverseShellService/StartSession',
                request_serializer=reverse__shell__pb2.CommandRequest.SerializeToString,
                response_deserializer=reverse__shell__pb2.CommandResponse.FromString,
                _registered_method=True)
        self.StreamResponses = channel.stream_stream(
                '/reverse_shell.ReverseShellService/StreamResponses',
                request_serializer=reverse__shell__pb2.CommandResponse.SerializeToString,
                response_deserializer=reverse__shell__pb2.CommandResponse.FromString,
                _registered_method=True)
        self.AddCommand = channel.unary_unary(
                '/reverse_shell.ReverseShellService/AddCommand',
                request_serializer=reverse__shell__pb2.CommandRequest.SerializeToString,
                response_deserializer=reverse__shell__pb2.Empty.FromString,
                _registered_method=True)
        self.GetResponse = channel.unary_stream(
                '/reverse_shell.ReverseShellService/GetResponse',
                request_serializer=reverse__shell__pb2.RequestID.SerializeToString,
                response_deserializer=reverse__shell__pb2.CommandResponse.FromString,
                _registered_method=True)


class ReverseShellServiceServicer(object):
    """The ReverseShellService definition.
    """

    def StartSession(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StreamResponses(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddCommand(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetResponse(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ReverseShellServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'StartSession': grpc.stream_stream_rpc_method_handler(
                    servicer.StartSession,
                    request_deserializer=reverse__shell__pb2.CommandRequest.FromString,
                    response_serializer=reverse__shell__pb2.CommandResponse.SerializeToString,
            ),
            'StreamResponses': grpc.stream_stream_rpc_method_handler(
                    servicer.StreamResponses,
                    request_deserializer=reverse__shell__pb2.CommandResponse.FromString,
                    response_serializer=reverse__shell__pb2.CommandResponse.SerializeToString,
            ),
            'AddCommand': grpc.unary_unary_rpc_method_handler(
                    servicer.AddCommand,
                    request_deserializer=reverse__shell__pb2.CommandRequest.FromString,
                    response_serializer=reverse__shell__pb2.Empty.SerializeToString,
            ),
            'GetResponse': grpc.unary_stream_rpc_method_handler(
                    servicer.GetResponse,
                    request_deserializer=reverse__shell__pb2.RequestID.FromString,
                    response_serializer=reverse__shell__pb2.CommandResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'reverse_shell.ReverseShellService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('reverse_shell.ReverseShellService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class ReverseShellService(object):
    """The ReverseShellService definition.
    """

    @staticmethod
    def StartSession(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(
            request_iterator,
            target,
            '/reverse_shell.ReverseShellService/StartSession',
            reverse__shell__pb2.CommandRequest.SerializeToString,
            reverse__shell__pb2.CommandResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def StreamResponses(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(
            request_iterator,
            target,
            '/reverse_shell.ReverseShellService/StreamResponses',
            reverse__shell__pb2.CommandResponse.SerializeToString,
            reverse__shell__pb2.CommandResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def AddCommand(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/reverse_shell.ReverseShellService/AddCommand',
            reverse__shell__pb2.CommandRequest.SerializeToString,
            reverse__shell__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetResponse(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/reverse_shell.ReverseShellService/GetResponse',
            reverse__shell__pb2.RequestID.SerializeToString,
            reverse__shell__pb2.CommandResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
