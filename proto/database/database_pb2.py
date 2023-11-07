# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: database.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x64\x61tabase.proto\x12\x1fopenfogstack.celestial.database\x1a\x1fgoogle/protobuf/timestamp.proto\"\x07\n\x05\x45mpty\"|\n\x11\x43onstellationInfo\x12\r\n\x05model\x18\x01 \x01(\t\x12\x0e\n\x06shells\x18\x02 \x01(\r\x12H\n\x0egroundstations\x18\x03 \x03(\x0b\x32\x30.openfogstack.celestial.database.GroundStationId\"\x1d\n\x0cShellRequest\x12\r\n\x05shell\x18\x01 \x01(\r\"\x85\x01\n\x0bSGP4Options\x12-\n\tstarttime\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\r\n\x05model\x18\x02 \x01(\t\x12\x0c\n\x04mode\x18\x03 \x01(\t\x12\r\n\x05\x62star\x18\x04 \x01(\x01\x12\x0c\n\x04ndot\x18\x05 \x01(\x01\x12\r\n\x05\x61rgpo\x18\x06 \x01(\x01\"\xa7\x01\n\rNetworkConfig\x12\x11\n\tbandwidth\x18\x01 \x01(\r\x12\x16\n\x0eislpropagation\x18\x02 \x01(\x01\x12\x18\n\x10mincommsaltitude\x18\x03 \x01(\r\x12\x14\n\x0cminelevation\x18\x04 \x01(\x01\x12\x16\n\x0egstpropagation\x18\x05 \x01(\x01\x12#\n\x1bgroundstationconnectiontype\x18\x06 \x01(\t\"d\n\rComputeConfig\x12\x0c\n\x04vcpu\x18\x01 \x01(\r\x12\x0b\n\x03mem\x18\x02 \x01(\r\x12\n\n\x02ht\x18\x03 \x01(\x08\x12\x0c\n\x04\x64isk\x18\x04 \x01(\r\x12\x0e\n\x06kernel\x18\x05 \x01(\t\x12\x0e\n\x06rootfs\x18\x06 \x01(\t\"\x92\x03\n\tShellInfo\x12\x0e\n\x06planes\x18\x01 \x01(\r\x12\x0c\n\x04sats\x18\x02 \x01(\r\x12\x10\n\x08\x61ltitude\x18\x03 \x01(\x01\x12\x13\n\x0binclination\x18\x04 \x01(\x01\x12\x1c\n\x14\x61rcofascendingsnodes\x18\x05 \x01(\x01\x12\x14\n\x0c\x65\x63\x63\x65ntricity\x18\x06 \x01(\x01\x12@\n\nactiveSats\x18\x07 \x03(\x0b\x32,.openfogstack.celestial.database.SatelliteId\x12?\n\x07network\x18\x08 \x01(\x0b\x32..openfogstack.celestial.database.NetworkConfig\x12?\n\x07\x63ompute\x18\t \x01(\x0b\x32..openfogstack.celestial.database.ComputeConfig\x12?\n\x04sgp4\x18\n \x01(\x0b\x32,.openfogstack.celestial.database.SGP4OptionsH\x00\x88\x01\x01\x42\x07\n\x05_sgp4\")\n\x0bSatelliteId\x12\r\n\x05shell\x18\x01 \x01(\r\x12\x0b\n\x03sat\x18\x02 \x01(\r\"&\n\x03Pos\x12\t\n\x01x\x18\x01 \x01(\x01\x12\t\n\x01y\x18\x02 \x01(\x01\x12\t\n\x01z\x18\x03 \x01(\x01\"\xe9\x01\n\rSatelliteInfo\x12\x36\n\x08position\x18\x01 \x01(\x0b\x32$.openfogstack.celestial.database.Pos\x12\x0e\n\x06\x61\x63tive\x18\x02 \x01(\x08\x12H\n\rconnectedSats\x18\x03 \x03(\x0b\x32\x31.openfogstack.celestial.database.ConnectedSatInfo\x12\x46\n\x0c\x63onnectedGST\x18\x04 \x03(\x0b\x32\x30.openfogstack.celestial.database.GroundStationId\"\x81\x01\n\x10\x43onnectedSatInfo\x12\x39\n\x03sat\x18\x01 \x01(\x0b\x32,.openfogstack.celestial.database.SatelliteId\x12\x10\n\x08\x64istance\x18\x02 \x01(\x01\x12\r\n\x05\x64\x65lay\x18\x03 \x01(\x01\x12\x11\n\tbandwidth\x18\x04 \x01(\x01\"\x85\x01\n\x10\x43onnectedGSTInfo\x12=\n\x03gst\x18\x01 \x01(\x0b\x32\x30.openfogstack.celestial.database.GroundStationId\x12\x10\n\x08\x64istance\x18\x02 \x01(\x01\x12\r\n\x05\x64\x65lay\x18\x03 \x01(\x01\x12\x11\n\tbandwidth\x18\x04 \x01(\x01\"\x1f\n\x0fGroundStationId\x12\x0c\n\x04name\x18\x01 \x01(\t\"\xbc\x02\n\x11GroundStationInfo\x12\x36\n\x08position\x18\x01 \x01(\x0b\x32$.openfogstack.celestial.database.Pos\x12\x10\n\x08latitude\x18\x02 \x01(\x01\x12\x11\n\tlongitude\x18\x03 \x01(\x01\x12?\n\x07network\x18\x04 \x01(\x0b\x32..openfogstack.celestial.database.NetworkConfig\x12?\n\x07\x63ompute\x18\x05 \x01(\x0b\x32..openfogstack.celestial.database.ComputeConfig\x12H\n\rconnectedSats\x18\x06 \x03(\x0b\x32\x31.openfogstack.celestial.database.ConnectedSatInfo\"\x8d\x01\n\x07Segment\x12\x13\n\x0bsourceShell\x18\x01 \x01(\x05\x12\x11\n\tsourceSat\x18\x02 \x01(\r\x12\x13\n\x0btargetShell\x18\x03 \x01(\x05\x12\x11\n\ttargetSat\x18\x04 \x01(\r\x12\r\n\x05\x64\x65lay\x18\x05 \x01(\x01\x12\x10\n\x08\x64istance\x18\x06 \x01(\x01\x12\x11\n\tbandwidth\x18\x07 \x01(\x01\"]\n\x0bPathRequest\x12\x13\n\x0bsourceShell\x18\x01 \x01(\x05\x12\x11\n\tsourceSat\x18\x02 \x01(\r\x12\x13\n\x0btargetShell\x18\x03 \x01(\x05\x12\x11\n\ttargetSat\x18\x04 \x01(\r\"@\n\x08PathInfo\x12\x34\n\x05paths\x18\x01 \x03(\x0b\x32%.openfogstack.celestial.database.Path\"v\n\x04Path\x12\x10\n\x08\x64istance\x18\x01 \x01(\x01\x12\r\n\x05\x64\x65lay\x18\x02 \x01(\x01\x12\x11\n\tbandwidth\x18\x03 \x01(\x01\x12:\n\x08segments\x18\x04 \x03(\x0b\x32(.openfogstack.celestial.database.Segment2\x9e\x04\n\x08\x44\x61tabase\x12k\n\rConstellation\x12&.openfogstack.celestial.database.Empty\x1a\x32.openfogstack.celestial.database.ConstellationInfo\x12\x62\n\x05Shell\x12-.openfogstack.celestial.database.ShellRequest\x1a*.openfogstack.celestial.database.ShellInfo\x12i\n\tSatellite\x12,.openfogstack.celestial.database.SatelliteId\x1a..openfogstack.celestial.database.SatelliteInfo\x12u\n\rGroundStation\x12\x30.openfogstack.celestial.database.GroundStationId\x1a\x32.openfogstack.celestial.database.GroundStationInfo\x12_\n\x04Path\x12,.openfogstack.celestial.database.PathRequest\x1a).openfogstack.celestial.database.PathInfoB\rZ\x0b./;databaseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'database_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z\013./;database'
  _globals['_EMPTY']._serialized_start=84
  _globals['_EMPTY']._serialized_end=91
  _globals['_CONSTELLATIONINFO']._serialized_start=93
  _globals['_CONSTELLATIONINFO']._serialized_end=217
  _globals['_SHELLREQUEST']._serialized_start=219
  _globals['_SHELLREQUEST']._serialized_end=248
  _globals['_SGP4OPTIONS']._serialized_start=251
  _globals['_SGP4OPTIONS']._serialized_end=384
  _globals['_NETWORKCONFIG']._serialized_start=387
  _globals['_NETWORKCONFIG']._serialized_end=554
  _globals['_COMPUTECONFIG']._serialized_start=556
  _globals['_COMPUTECONFIG']._serialized_end=656
  _globals['_SHELLINFO']._serialized_start=659
  _globals['_SHELLINFO']._serialized_end=1061
  _globals['_SATELLITEID']._serialized_start=1063
  _globals['_SATELLITEID']._serialized_end=1104
  _globals['_POS']._serialized_start=1106
  _globals['_POS']._serialized_end=1144
  _globals['_SATELLITEINFO']._serialized_start=1147
  _globals['_SATELLITEINFO']._serialized_end=1380
  _globals['_CONNECTEDSATINFO']._serialized_start=1383
  _globals['_CONNECTEDSATINFO']._serialized_end=1512
  _globals['_CONNECTEDGSTINFO']._serialized_start=1515
  _globals['_CONNECTEDGSTINFO']._serialized_end=1648
  _globals['_GROUNDSTATIONID']._serialized_start=1650
  _globals['_GROUNDSTATIONID']._serialized_end=1681
  _globals['_GROUNDSTATIONINFO']._serialized_start=1684
  _globals['_GROUNDSTATIONINFO']._serialized_end=2000
  _globals['_SEGMENT']._serialized_start=2003
  _globals['_SEGMENT']._serialized_end=2144
  _globals['_PATHREQUEST']._serialized_start=2146
  _globals['_PATHREQUEST']._serialized_end=2239
  _globals['_PATHINFO']._serialized_start=2241
  _globals['_PATHINFO']._serialized_end=2305
  _globals['_PATH']._serialized_start=2307
  _globals['_PATH']._serialized_end=2425
  _globals['_DATABASE']._serialized_start=2428
  _globals['_DATABASE']._serialized_end=2970
# @@protoc_insertion_point(module_scope)
