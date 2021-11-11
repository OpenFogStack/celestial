# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: celestial.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='celestial.proto',
  package='openfogstack.celestial.celestial',
  syntax='proto3',
  serialized_options=b'Z\013.;celestial',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0f\x63\x65lestial.proto\x12 openfogstack.celestial.celestial\"\x07\n\x05\x45mpty\"$\n\x08HostInfo\x12\x0b\n\x03\x63pu\x18\x01 \x01(\x04\x12\x0b\n\x03mem\x18\x02 \x01(\x04\"+\n\tReadyInfo\x12\r\n\x05ready\x18\x01 \x01(\x08\x12\x0f\n\x07\x63reated\x18\x02 \x01(\x04\"#\n\x05Shell\x12\n\n\x02id\x18\x01 \x01(\x04\x12\x0e\n\x06planes\x18\x02 \x01(\x04\"\x82\x01\n\x0bInitRequest\x12\x10\n\x08\x64\x61tabase\x18\x01 \x01(\x08\x12\x14\n\x0c\x64\x61tabaseHost\x18\x02 \x01(\t\x12\x12\n\nshellcount\x18\x03 \x01(\x04\x12\x37\n\x06shells\x18\x04 \x03(\x0b\x32\'.openfogstack.celestial.celestial.Shell\")\n\nRemoteHost\x12\r\n\x05index\x18\x01 \x01(\x04\x12\x0c\n\x04\x61\x64\x64r\x18\x02 \x01(\t\"f\n\x12InitRemotesRequest\x12\r\n\x05index\x18\x01 \x01(\x04\x12\x41\n\x0bremotehosts\x18\x02 \x03(\x0b\x32,.openfogstack.celestial.celestial.RemoteHost\"2\n\x07Machine\x12\r\n\x05shell\x18\x01 \x01(\x03\x12\n\n\x02id\x18\x02 \x01(\x04\x12\x0c\n\x04name\x18\x03 \x01(\t\"|\n\x11\x46irecrackerConfig\x12\x0c\n\x04vcpu\x18\x01 \x01(\x04\x12\x0b\n\x03mem\x18\x02 \x01(\x04\x12\n\n\x02ht\x18\x03 \x01(\x08\x12\x0c\n\x04\x64isk\x18\x04 \x01(\x04\x12\x0e\n\x06kernel\x18\x05 \x01(\t\x12\x0e\n\x06rootfs\x18\x06 \x01(\t\x12\x12\n\nbootparams\x18\x07 \x01(\t\"\"\n\rNetworkConfig\x12\x11\n\tbandwidth\x18\x01 \x01(\x04\"\xfa\x01\n\x14\x43reateMachineRequest\x12:\n\x07machine\x18\x01 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\x12N\n\x11\x66irecrackerconfig\x18\x02 \x01(\x0b\x32\x33.openfogstack.celestial.celestial.FirecrackerConfig\x12\x46\n\rnetworkconfig\x18\x03 \x01(\x0b\x32/.openfogstack.celestial.celestial.NetworkConfig\x12\x0e\n\x06status\x18\x04 \x01(\x08\"\xa0\x01\n\x1a\x43reateRemoteMachineRequest\x12:\n\x07machine\x18\x01 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\x12\x46\n\rnetworkconfig\x18\x03 \x01(\x0b\x32/.openfogstack.celestial.celestial.NetworkConfig\"b\n\x14ModifyMachineRequest\x12:\n\x07machine\x18\x01 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\x12\x0e\n\x06status\x18\x02 \x01(\x08\"\xd4\x01\n\x12ModifyLinksRequest\x12\x34\n\x01\x61\x18\x01 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\x12\x43\n\x06remove\x18\x02 \x03(\x0b\x32\x33.openfogstack.celestial.celestial.RemoveLinkRequest\x12\x43\n\x06modify\x18\x03 \x03(\x0b\x32\x33.openfogstack.celestial.celestial.ModifyLinkRequest\"I\n\x11RemoveLinkRequest\x12\x34\n\x01\x62\x18\x02 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\"m\n\x11ModifyLinkRequest\x12\x34\n\x01\x62\x18\x02 \x01(\x0b\x32).openfogstack.celestial.celestial.Machine\x12\x0f\n\x07latency\x18\x03 \x01(\x01\x12\x11\n\tbandwidth\x18\x04 \x01(\x04\x32\xd4\x06\n\tCelestial\x12\x62\n\x0bGetHostInfo\x12\'.openfogstack.celestial.celestial.Empty\x1a*.openfogstack.celestial.celestial.HostInfo\x12\x61\n\tHostReady\x12\'.openfogstack.celestial.celestial.Empty\x1a+.openfogstack.celestial.celestial.ReadyInfo\x12^\n\x04Init\x12-.openfogstack.celestial.celestial.InitRequest\x1a\'.openfogstack.celestial.celestial.Empty\x12l\n\x0bInitRemotes\x12\x34.openfogstack.celestial.celestial.InitRemotesRequest\x1a\'.openfogstack.celestial.celestial.Empty\x12`\n\x0cStartPeering\x12\'.openfogstack.celestial.celestial.Empty\x1a\'.openfogstack.celestial.celestial.Empty\x12p\n\rCreateMachine\x12\x36.openfogstack.celestial.celestial.CreateMachineRequest\x1a\'.openfogstack.celestial.celestial.Empty\x12p\n\rModifyMachine\x12\x36.openfogstack.celestial.celestial.ModifyMachineRequest\x1a\'.openfogstack.celestial.celestial.Empty\x12l\n\x0bModifyLinks\x12\x34.openfogstack.celestial.celestial.ModifyLinksRequest\x1a\'.openfogstack.celestial.celestial.EmptyB\rZ\x0b.;celestialb\x06proto3'
)




_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='openfogstack.celestial.celestial.Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=53,
  serialized_end=60,
)


_HOSTINFO = _descriptor.Descriptor(
  name='HostInfo',
  full_name='openfogstack.celestial.celestial.HostInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='cpu', full_name='openfogstack.celestial.celestial.HostInfo.cpu', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='mem', full_name='openfogstack.celestial.celestial.HostInfo.mem', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=62,
  serialized_end=98,
)


_READYINFO = _descriptor.Descriptor(
  name='ReadyInfo',
  full_name='openfogstack.celestial.celestial.ReadyInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ready', full_name='openfogstack.celestial.celestial.ReadyInfo.ready', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='created', full_name='openfogstack.celestial.celestial.ReadyInfo.created', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=100,
  serialized_end=143,
)


_SHELL = _descriptor.Descriptor(
  name='Shell',
  full_name='openfogstack.celestial.celestial.Shell',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='openfogstack.celestial.celestial.Shell.id', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='planes', full_name='openfogstack.celestial.celestial.Shell.planes', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=145,
  serialized_end=180,
)


_INITREQUEST = _descriptor.Descriptor(
  name='InitRequest',
  full_name='openfogstack.celestial.celestial.InitRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='database', full_name='openfogstack.celestial.celestial.InitRequest.database', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='databaseHost', full_name='openfogstack.celestial.celestial.InitRequest.databaseHost', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='shellcount', full_name='openfogstack.celestial.celestial.InitRequest.shellcount', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='shells', full_name='openfogstack.celestial.celestial.InitRequest.shells', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=183,
  serialized_end=313,
)


_REMOTEHOST = _descriptor.Descriptor(
  name='RemoteHost',
  full_name='openfogstack.celestial.celestial.RemoteHost',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='index', full_name='openfogstack.celestial.celestial.RemoteHost.index', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='addr', full_name='openfogstack.celestial.celestial.RemoteHost.addr', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=315,
  serialized_end=356,
)


_INITREMOTESREQUEST = _descriptor.Descriptor(
  name='InitRemotesRequest',
  full_name='openfogstack.celestial.celestial.InitRemotesRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='index', full_name='openfogstack.celestial.celestial.InitRemotesRequest.index', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='remotehosts', full_name='openfogstack.celestial.celestial.InitRemotesRequest.remotehosts', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=358,
  serialized_end=460,
)


_MACHINE = _descriptor.Descriptor(
  name='Machine',
  full_name='openfogstack.celestial.celestial.Machine',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='shell', full_name='openfogstack.celestial.celestial.Machine.shell', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='openfogstack.celestial.celestial.Machine.id', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='name', full_name='openfogstack.celestial.celestial.Machine.name', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=462,
  serialized_end=512,
)


_FIRECRACKERCONFIG = _descriptor.Descriptor(
  name='FirecrackerConfig',
  full_name='openfogstack.celestial.celestial.FirecrackerConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='vcpu', full_name='openfogstack.celestial.celestial.FirecrackerConfig.vcpu', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='mem', full_name='openfogstack.celestial.celestial.FirecrackerConfig.mem', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ht', full_name='openfogstack.celestial.celestial.FirecrackerConfig.ht', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk', full_name='openfogstack.celestial.celestial.FirecrackerConfig.disk', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='kernel', full_name='openfogstack.celestial.celestial.FirecrackerConfig.kernel', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rootfs', full_name='openfogstack.celestial.celestial.FirecrackerConfig.rootfs', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bootparams', full_name='openfogstack.celestial.celestial.FirecrackerConfig.bootparams', index=6,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=514,
  serialized_end=638,
)


_NETWORKCONFIG = _descriptor.Descriptor(
  name='NetworkConfig',
  full_name='openfogstack.celestial.celestial.NetworkConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='bandwidth', full_name='openfogstack.celestial.celestial.NetworkConfig.bandwidth', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=640,
  serialized_end=674,
)


_CREATEMACHINEREQUEST = _descriptor.Descriptor(
  name='CreateMachineRequest',
  full_name='openfogstack.celestial.celestial.CreateMachineRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='machine', full_name='openfogstack.celestial.celestial.CreateMachineRequest.machine', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='firecrackerconfig', full_name='openfogstack.celestial.celestial.CreateMachineRequest.firecrackerconfig', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='networkconfig', full_name='openfogstack.celestial.celestial.CreateMachineRequest.networkconfig', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='status', full_name='openfogstack.celestial.celestial.CreateMachineRequest.status', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=677,
  serialized_end=927,
)


_CREATEREMOTEMACHINEREQUEST = _descriptor.Descriptor(
  name='CreateRemoteMachineRequest',
  full_name='openfogstack.celestial.celestial.CreateRemoteMachineRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='machine', full_name='openfogstack.celestial.celestial.CreateRemoteMachineRequest.machine', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='networkconfig', full_name='openfogstack.celestial.celestial.CreateRemoteMachineRequest.networkconfig', index=1,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=930,
  serialized_end=1090,
)


_MODIFYMACHINEREQUEST = _descriptor.Descriptor(
  name='ModifyMachineRequest',
  full_name='openfogstack.celestial.celestial.ModifyMachineRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='machine', full_name='openfogstack.celestial.celestial.ModifyMachineRequest.machine', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='status', full_name='openfogstack.celestial.celestial.ModifyMachineRequest.status', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1092,
  serialized_end=1190,
)


_MODIFYLINKSREQUEST = _descriptor.Descriptor(
  name='ModifyLinksRequest',
  full_name='openfogstack.celestial.celestial.ModifyLinksRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='a', full_name='openfogstack.celestial.celestial.ModifyLinksRequest.a', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='remove', full_name='openfogstack.celestial.celestial.ModifyLinksRequest.remove', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='modify', full_name='openfogstack.celestial.celestial.ModifyLinksRequest.modify', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1193,
  serialized_end=1405,
)


_REMOVELINKREQUEST = _descriptor.Descriptor(
  name='RemoveLinkRequest',
  full_name='openfogstack.celestial.celestial.RemoveLinkRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b', full_name='openfogstack.celestial.celestial.RemoveLinkRequest.b', index=0,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1407,
  serialized_end=1480,
)


_MODIFYLINKREQUEST = _descriptor.Descriptor(
  name='ModifyLinkRequest',
  full_name='openfogstack.celestial.celestial.ModifyLinkRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b', full_name='openfogstack.celestial.celestial.ModifyLinkRequest.b', index=0,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='latency', full_name='openfogstack.celestial.celestial.ModifyLinkRequest.latency', index=1,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bandwidth', full_name='openfogstack.celestial.celestial.ModifyLinkRequest.bandwidth', index=2,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1482,
  serialized_end=1591,
)

_INITREQUEST.fields_by_name['shells'].message_type = _SHELL
_INITREMOTESREQUEST.fields_by_name['remotehosts'].message_type = _REMOTEHOST
_CREATEMACHINEREQUEST.fields_by_name['machine'].message_type = _MACHINE
_CREATEMACHINEREQUEST.fields_by_name['firecrackerconfig'].message_type = _FIRECRACKERCONFIG
_CREATEMACHINEREQUEST.fields_by_name['networkconfig'].message_type = _NETWORKCONFIG
_CREATEREMOTEMACHINEREQUEST.fields_by_name['machine'].message_type = _MACHINE
_CREATEREMOTEMACHINEREQUEST.fields_by_name['networkconfig'].message_type = _NETWORKCONFIG
_MODIFYMACHINEREQUEST.fields_by_name['machine'].message_type = _MACHINE
_MODIFYLINKSREQUEST.fields_by_name['a'].message_type = _MACHINE
_MODIFYLINKSREQUEST.fields_by_name['remove'].message_type = _REMOVELINKREQUEST
_MODIFYLINKSREQUEST.fields_by_name['modify'].message_type = _MODIFYLINKREQUEST
_REMOVELINKREQUEST.fields_by_name['b'].message_type = _MACHINE
_MODIFYLINKREQUEST.fields_by_name['b'].message_type = _MACHINE
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
DESCRIPTOR.message_types_by_name['HostInfo'] = _HOSTINFO
DESCRIPTOR.message_types_by_name['ReadyInfo'] = _READYINFO
DESCRIPTOR.message_types_by_name['Shell'] = _SHELL
DESCRIPTOR.message_types_by_name['InitRequest'] = _INITREQUEST
DESCRIPTOR.message_types_by_name['RemoteHost'] = _REMOTEHOST
DESCRIPTOR.message_types_by_name['InitRemotesRequest'] = _INITREMOTESREQUEST
DESCRIPTOR.message_types_by_name['Machine'] = _MACHINE
DESCRIPTOR.message_types_by_name['FirecrackerConfig'] = _FIRECRACKERCONFIG
DESCRIPTOR.message_types_by_name['NetworkConfig'] = _NETWORKCONFIG
DESCRIPTOR.message_types_by_name['CreateMachineRequest'] = _CREATEMACHINEREQUEST
DESCRIPTOR.message_types_by_name['CreateRemoteMachineRequest'] = _CREATEREMOTEMACHINEREQUEST
DESCRIPTOR.message_types_by_name['ModifyMachineRequest'] = _MODIFYMACHINEREQUEST
DESCRIPTOR.message_types_by_name['ModifyLinksRequest'] = _MODIFYLINKSREQUEST
DESCRIPTOR.message_types_by_name['RemoveLinkRequest'] = _REMOVELINKREQUEST
DESCRIPTOR.message_types_by_name['ModifyLinkRequest'] = _MODIFYLINKREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.Empty)
  })
_sym_db.RegisterMessage(Empty)

HostInfo = _reflection.GeneratedProtocolMessageType('HostInfo', (_message.Message,), {
  'DESCRIPTOR' : _HOSTINFO,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.HostInfo)
  })
_sym_db.RegisterMessage(HostInfo)

ReadyInfo = _reflection.GeneratedProtocolMessageType('ReadyInfo', (_message.Message,), {
  'DESCRIPTOR' : _READYINFO,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.ReadyInfo)
  })
_sym_db.RegisterMessage(ReadyInfo)

Shell = _reflection.GeneratedProtocolMessageType('Shell', (_message.Message,), {
  'DESCRIPTOR' : _SHELL,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.Shell)
  })
_sym_db.RegisterMessage(Shell)

InitRequest = _reflection.GeneratedProtocolMessageType('InitRequest', (_message.Message,), {
  'DESCRIPTOR' : _INITREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.InitRequest)
  })
_sym_db.RegisterMessage(InitRequest)

RemoteHost = _reflection.GeneratedProtocolMessageType('RemoteHost', (_message.Message,), {
  'DESCRIPTOR' : _REMOTEHOST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.RemoteHost)
  })
_sym_db.RegisterMessage(RemoteHost)

InitRemotesRequest = _reflection.GeneratedProtocolMessageType('InitRemotesRequest', (_message.Message,), {
  'DESCRIPTOR' : _INITREMOTESREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.InitRemotesRequest)
  })
_sym_db.RegisterMessage(InitRemotesRequest)

Machine = _reflection.GeneratedProtocolMessageType('Machine', (_message.Message,), {
  'DESCRIPTOR' : _MACHINE,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.Machine)
  })
_sym_db.RegisterMessage(Machine)

FirecrackerConfig = _reflection.GeneratedProtocolMessageType('FirecrackerConfig', (_message.Message,), {
  'DESCRIPTOR' : _FIRECRACKERCONFIG,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.FirecrackerConfig)
  })
_sym_db.RegisterMessage(FirecrackerConfig)

NetworkConfig = _reflection.GeneratedProtocolMessageType('NetworkConfig', (_message.Message,), {
  'DESCRIPTOR' : _NETWORKCONFIG,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.NetworkConfig)
  })
_sym_db.RegisterMessage(NetworkConfig)

CreateMachineRequest = _reflection.GeneratedProtocolMessageType('CreateMachineRequest', (_message.Message,), {
  'DESCRIPTOR' : _CREATEMACHINEREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.CreateMachineRequest)
  })
_sym_db.RegisterMessage(CreateMachineRequest)

CreateRemoteMachineRequest = _reflection.GeneratedProtocolMessageType('CreateRemoteMachineRequest', (_message.Message,), {
  'DESCRIPTOR' : _CREATEREMOTEMACHINEREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.CreateRemoteMachineRequest)
  })
_sym_db.RegisterMessage(CreateRemoteMachineRequest)

ModifyMachineRequest = _reflection.GeneratedProtocolMessageType('ModifyMachineRequest', (_message.Message,), {
  'DESCRIPTOR' : _MODIFYMACHINEREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.ModifyMachineRequest)
  })
_sym_db.RegisterMessage(ModifyMachineRequest)

ModifyLinksRequest = _reflection.GeneratedProtocolMessageType('ModifyLinksRequest', (_message.Message,), {
  'DESCRIPTOR' : _MODIFYLINKSREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.ModifyLinksRequest)
  })
_sym_db.RegisterMessage(ModifyLinksRequest)

RemoveLinkRequest = _reflection.GeneratedProtocolMessageType('RemoveLinkRequest', (_message.Message,), {
  'DESCRIPTOR' : _REMOVELINKREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.RemoveLinkRequest)
  })
_sym_db.RegisterMessage(RemoveLinkRequest)

ModifyLinkRequest = _reflection.GeneratedProtocolMessageType('ModifyLinkRequest', (_message.Message,), {
  'DESCRIPTOR' : _MODIFYLINKREQUEST,
  '__module__' : 'celestial_pb2'
  # @@protoc_insertion_point(class_scope:openfogstack.celestial.celestial.ModifyLinkRequest)
  })
_sym_db.RegisterMessage(ModifyLinkRequest)


DESCRIPTOR._options = None

_CELESTIAL = _descriptor.ServiceDescriptor(
  name='Celestial',
  full_name='openfogstack.celestial.celestial.Celestial',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=1594,
  serialized_end=2446,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetHostInfo',
    full_name='openfogstack.celestial.celestial.Celestial.GetHostInfo',
    index=0,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_HOSTINFO,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='HostReady',
    full_name='openfogstack.celestial.celestial.Celestial.HostReady',
    index=1,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_READYINFO,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Init',
    full_name='openfogstack.celestial.celestial.Celestial.Init',
    index=2,
    containing_service=None,
    input_type=_INITREQUEST,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='InitRemotes',
    full_name='openfogstack.celestial.celestial.Celestial.InitRemotes',
    index=3,
    containing_service=None,
    input_type=_INITREMOTESREQUEST,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='StartPeering',
    full_name='openfogstack.celestial.celestial.Celestial.StartPeering',
    index=4,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='CreateMachine',
    full_name='openfogstack.celestial.celestial.Celestial.CreateMachine',
    index=5,
    containing_service=None,
    input_type=_CREATEMACHINEREQUEST,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ModifyMachine',
    full_name='openfogstack.celestial.celestial.Celestial.ModifyMachine',
    index=6,
    containing_service=None,
    input_type=_MODIFYMACHINEREQUEST,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ModifyLinks',
    full_name='openfogstack.celestial.celestial.Celestial.ModifyLinks',
    index=7,
    containing_service=None,
    input_type=_MODIFYLINKSREQUEST,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_CELESTIAL)

DESCRIPTOR.services_by_name['Celestial'] = _CELESTIAL

# @@protoc_insertion_point(module_scope)
