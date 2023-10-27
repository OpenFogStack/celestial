# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import database_pb2 as database__pb2


class DatabaseStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Constellation = channel.unary_unary(
                '/openfogstack.celestial.database.Database/Constellation',
                request_serializer=database__pb2.Empty.SerializeToString,
                response_deserializer=database__pb2.ConstellationInfo.FromString,
                )
        self.Shell = channel.unary_unary(
                '/openfogstack.celestial.database.Database/Shell',
                request_serializer=database__pb2.ShellRequest.SerializeToString,
                response_deserializer=database__pb2.ShellInfo.FromString,
                )
        self.Satellite = channel.unary_unary(
                '/openfogstack.celestial.database.Database/Satellite',
                request_serializer=database__pb2.SatelliteId.SerializeToString,
                response_deserializer=database__pb2.SatelliteInfo.FromString,
                )
        self.GroundStation = channel.unary_unary(
                '/openfogstack.celestial.database.Database/GroundStation',
                request_serializer=database__pb2.GroundStationId.SerializeToString,
                response_deserializer=database__pb2.GroundStationInfo.FromString,
                )
        self.Path = channel.unary_unary(
                '/openfogstack.celestial.database.Database/Path',
                request_serializer=database__pb2.PathRequest.SerializeToString,
                response_deserializer=database__pb2.PathInfo.FromString,
                )


class DatabaseServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Constellation(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shell(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Satellite(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GroundStation(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Path(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DatabaseServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Constellation': grpc.unary_unary_rpc_method_handler(
                    servicer.Constellation,
                    request_deserializer=database__pb2.Empty.FromString,
                    response_serializer=database__pb2.ConstellationInfo.SerializeToString,
            ),
            'Shell': grpc.unary_unary_rpc_method_handler(
                    servicer.Shell,
                    request_deserializer=database__pb2.ShellRequest.FromString,
                    response_serializer=database__pb2.ShellInfo.SerializeToString,
            ),
            'Satellite': grpc.unary_unary_rpc_method_handler(
                    servicer.Satellite,
                    request_deserializer=database__pb2.SatelliteId.FromString,
                    response_serializer=database__pb2.SatelliteInfo.SerializeToString,
            ),
            'GroundStation': grpc.unary_unary_rpc_method_handler(
                    servicer.GroundStation,
                    request_deserializer=database__pb2.GroundStationId.FromString,
                    response_serializer=database__pb2.GroundStationInfo.SerializeToString,
            ),
            'Path': grpc.unary_unary_rpc_method_handler(
                    servicer.Path,
                    request_deserializer=database__pb2.PathRequest.FromString,
                    response_serializer=database__pb2.PathInfo.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'openfogstack.celestial.database.Database', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Database(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Constellation(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/openfogstack.celestial.database.Database/Constellation',
            database__pb2.Empty.SerializeToString,
            database__pb2.ConstellationInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Shell(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/openfogstack.celestial.database.Database/Shell',
            database__pb2.ShellRequest.SerializeToString,
            database__pb2.ShellInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Satellite(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/openfogstack.celestial.database.Database/Satellite',
            database__pb2.SatelliteId.SerializeToString,
            database__pb2.SatelliteInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GroundStation(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/openfogstack.celestial.database.Database/GroundStation',
            database__pb2.GroundStationId.SerializeToString,
            database__pb2.GroundStationInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Path(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/openfogstack.celestial.database.Database/Path',
            database__pb2.PathRequest.SerializeToString,
            database__pb2.PathInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)