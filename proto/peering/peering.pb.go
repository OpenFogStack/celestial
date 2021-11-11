//
// This file is part of Celestial (https://github.com/OpenFogStack/celestial).
// Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.27.1
// 	protoc        v3.17.3
// source: peering.proto

package peering

import (
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
	protoimpl "google.golang.org/protobuf/runtime/protoimpl"
	reflect "reflect"
	sync "sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

type Empty struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields
}

func (x *Empty) Reset() {
	*x = Empty{}
	if protoimpl.UnsafeEnabled {
		mi := &file_peering_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *Empty) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*Empty) ProtoMessage() {}

func (x *Empty) ProtoReflect() protoreflect.Message {
	mi := &file_peering_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use Empty.ProtoReflect.Descriptor instead.
func (*Empty) Descriptor() ([]byte, []int) {
	return file_peering_proto_rawDescGZIP(), []int{0}
}

type Machine struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	// allow -1 for ground stations
	Shell int64  `protobuf:"varint,1,opt,name=shell,proto3" json:"shell,omitempty"`
	Id    uint64 `protobuf:"varint,2,opt,name=id,proto3" json:"id,omitempty"`
	// name is only used for ground stations
	Name string `protobuf:"bytes,3,opt,name=name,proto3" json:"name,omitempty"`
}

func (x *Machine) Reset() {
	*x = Machine{}
	if protoimpl.UnsafeEnabled {
		mi := &file_peering_proto_msgTypes[1]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *Machine) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*Machine) ProtoMessage() {}

func (x *Machine) ProtoReflect() protoreflect.Message {
	mi := &file_peering_proto_msgTypes[1]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use Machine.ProtoReflect.Descriptor instead.
func (*Machine) Descriptor() ([]byte, []int) {
	return file_peering_proto_rawDescGZIP(), []int{1}
}

func (x *Machine) GetShell() int64 {
	if x != nil {
		return x.Shell
	}
	return 0
}

func (x *Machine) GetId() uint64 {
	if x != nil {
		return x.Id
	}
	return 0
}

func (x *Machine) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

type StartPeerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Publickey string `protobuf:"bytes,1,opt,name=publickey,proto3" json:"publickey,omitempty"`
	Index     uint64 `protobuf:"varint,2,opt,name=index,proto3" json:"index,omitempty"`
}

func (x *StartPeerRequest) Reset() {
	*x = StartPeerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_peering_proto_msgTypes[2]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StartPeerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StartPeerRequest) ProtoMessage() {}

func (x *StartPeerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_peering_proto_msgTypes[2]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StartPeerRequest.ProtoReflect.Descriptor instead.
func (*StartPeerRequest) Descriptor() ([]byte, []int) {
	return file_peering_proto_rawDescGZIP(), []int{2}
}

func (x *StartPeerRequest) GetPublickey() string {
	if x != nil {
		return x.Publickey
	}
	return ""
}

func (x *StartPeerRequest) GetIndex() uint64 {
	if x != nil {
		return x.Index
	}
	return 0
}

type RouteRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Machine   *Machine `protobuf:"bytes,1,opt,name=machine,proto3" json:"machine,omitempty"`
	Index     uint64   `protobuf:"varint,2,opt,name=index,proto3" json:"index,omitempty"`
	Bandwidth uint64   `protobuf:"varint,3,opt,name=bandwidth,proto3" json:"bandwidth,omitempty"`
}

func (x *RouteRequest) Reset() {
	*x = RouteRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_peering_proto_msgTypes[3]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *RouteRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*RouteRequest) ProtoMessage() {}

func (x *RouteRequest) ProtoReflect() protoreflect.Message {
	mi := &file_peering_proto_msgTypes[3]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use RouteRequest.ProtoReflect.Descriptor instead.
func (*RouteRequest) Descriptor() ([]byte, []int) {
	return file_peering_proto_rawDescGZIP(), []int{3}
}

func (x *RouteRequest) GetMachine() *Machine {
	if x != nil {
		return x.Machine
	}
	return nil
}

func (x *RouteRequest) GetIndex() uint64 {
	if x != nil {
		return x.Index
	}
	return 0
}

func (x *RouteRequest) GetBandwidth() uint64 {
	if x != nil {
		return x.Bandwidth
	}
	return 0
}

var File_peering_proto protoreflect.FileDescriptor

var file_peering_proto_rawDesc = []byte{
	0x0a, 0x0d, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x12,
	0x1e, 0x6f, 0x70, 0x65, 0x6e, 0x66, 0x6f, 0x67, 0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65,
	0x6c, 0x65, 0x73, 0x74, 0x69, 0x61, 0x6c, 0x2e, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x22,
	0x07, 0x0a, 0x05, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x22, 0x43, 0x0a, 0x07, 0x4d, 0x61, 0x63, 0x68,
	0x69, 0x6e, 0x65, 0x12, 0x14, 0x0a, 0x05, 0x73, 0x68, 0x65, 0x6c, 0x6c, 0x18, 0x01, 0x20, 0x01,
	0x28, 0x03, 0x52, 0x05, 0x73, 0x68, 0x65, 0x6c, 0x6c, 0x12, 0x0e, 0x0a, 0x02, 0x69, 0x64, 0x18,
	0x02, 0x20, 0x01, 0x28, 0x04, 0x52, 0x02, 0x69, 0x64, 0x12, 0x12, 0x0a, 0x04, 0x6e, 0x61, 0x6d,
	0x65, 0x18, 0x03, 0x20, 0x01, 0x28, 0x09, 0x52, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x22, 0x46, 0x0a,
	0x10, 0x53, 0x74, 0x61, 0x72, 0x74, 0x50, 0x65, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x12, 0x1c, 0x0a, 0x09, 0x70, 0x75, 0x62, 0x6c, 0x69, 0x63, 0x6b, 0x65, 0x79, 0x18, 0x01,
	0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x70, 0x75, 0x62, 0x6c, 0x69, 0x63, 0x6b, 0x65, 0x79, 0x12,
	0x14, 0x0a, 0x05, 0x69, 0x6e, 0x64, 0x65, 0x78, 0x18, 0x02, 0x20, 0x01, 0x28, 0x04, 0x52, 0x05,
	0x69, 0x6e, 0x64, 0x65, 0x78, 0x22, 0x85, 0x01, 0x0a, 0x0c, 0x52, 0x6f, 0x75, 0x74, 0x65, 0x52,
	0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x41, 0x0a, 0x07, 0x6d, 0x61, 0x63, 0x68, 0x69, 0x6e,
	0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x27, 0x2e, 0x6f, 0x70, 0x65, 0x6e, 0x66, 0x6f,
	0x67, 0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65, 0x6c, 0x65, 0x73, 0x74, 0x69, 0x61, 0x6c,
	0x2e, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x4d, 0x61, 0x63, 0x68, 0x69, 0x6e, 0x65,
	0x52, 0x07, 0x6d, 0x61, 0x63, 0x68, 0x69, 0x6e, 0x65, 0x12, 0x14, 0x0a, 0x05, 0x69, 0x6e, 0x64,
	0x65, 0x78, 0x18, 0x02, 0x20, 0x01, 0x28, 0x04, 0x52, 0x05, 0x69, 0x6e, 0x64, 0x65, 0x78, 0x12,
	0x1c, 0x0a, 0x09, 0x62, 0x61, 0x6e, 0x64, 0x77, 0x69, 0x64, 0x74, 0x68, 0x18, 0x03, 0x20, 0x01,
	0x28, 0x04, 0x52, 0x09, 0x62, 0x61, 0x6e, 0x64, 0x77, 0x69, 0x64, 0x74, 0x68, 0x32, 0xcd, 0x01,
	0x0a, 0x07, 0x50, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x12, 0x64, 0x0a, 0x09, 0x53, 0x74, 0x61,
	0x72, 0x74, 0x50, 0x65, 0x65, 0x72, 0x12, 0x30, 0x2e, 0x6f, 0x70, 0x65, 0x6e, 0x66, 0x6f, 0x67,
	0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65, 0x6c, 0x65, 0x73, 0x74, 0x69, 0x61, 0x6c, 0x2e,
	0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x53, 0x74, 0x61, 0x72, 0x74, 0x50, 0x65, 0x65,
	0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x25, 0x2e, 0x6f, 0x70, 0x65, 0x6e, 0x66,
	0x6f, 0x67, 0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65, 0x6c, 0x65, 0x73, 0x74, 0x69, 0x61,
	0x6c, 0x2e, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x12,
	0x5c, 0x0a, 0x05, 0x52, 0x6f, 0x75, 0x74, 0x65, 0x12, 0x2c, 0x2e, 0x6f, 0x70, 0x65, 0x6e, 0x66,
	0x6f, 0x67, 0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65, 0x6c, 0x65, 0x73, 0x74, 0x69, 0x61,
	0x6c, 0x2e, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x52, 0x6f, 0x75, 0x74, 0x65, 0x52,
	0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x25, 0x2e, 0x6f, 0x70, 0x65, 0x6e, 0x66, 0x6f, 0x67,
	0x73, 0x74, 0x61, 0x63, 0x6b, 0x2e, 0x63, 0x65, 0x6c, 0x65, 0x73, 0x74, 0x69, 0x61, 0x6c, 0x2e,
	0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x42, 0x0b, 0x5a,
	0x09, 0x2e, 0x3b, 0x70, 0x65, 0x65, 0x72, 0x69, 0x6e, 0x67, 0x62, 0x06, 0x70, 0x72, 0x6f, 0x74,
	0x6f, 0x33,
}

var (
	file_peering_proto_rawDescOnce sync.Once
	file_peering_proto_rawDescData = file_peering_proto_rawDesc
)

func file_peering_proto_rawDescGZIP() []byte {
	file_peering_proto_rawDescOnce.Do(func() {
		file_peering_proto_rawDescData = protoimpl.X.CompressGZIP(file_peering_proto_rawDescData)
	})
	return file_peering_proto_rawDescData
}

var file_peering_proto_msgTypes = make([]protoimpl.MessageInfo, 4)
var file_peering_proto_goTypes = []interface{}{
	(*Empty)(nil),            // 0: openfogstack.celestial.peering.Empty
	(*Machine)(nil),          // 1: openfogstack.celestial.peering.Machine
	(*StartPeerRequest)(nil), // 2: openfogstack.celestial.peering.StartPeerRequest
	(*RouteRequest)(nil),     // 3: openfogstack.celestial.peering.RouteRequest
}
var file_peering_proto_depIdxs = []int32{
	1, // 0: openfogstack.celestial.peering.RouteRequest.machine:type_name -> openfogstack.celestial.peering.Machine
	2, // 1: openfogstack.celestial.peering.Peering.StartPeer:input_type -> openfogstack.celestial.peering.StartPeerRequest
	3, // 2: openfogstack.celestial.peering.Peering.Route:input_type -> openfogstack.celestial.peering.RouteRequest
	0, // 3: openfogstack.celestial.peering.Peering.StartPeer:output_type -> openfogstack.celestial.peering.Empty
	0, // 4: openfogstack.celestial.peering.Peering.Route:output_type -> openfogstack.celestial.peering.Empty
	3, // [3:5] is the sub-list for method output_type
	1, // [1:3] is the sub-list for method input_type
	1, // [1:1] is the sub-list for extension type_name
	1, // [1:1] is the sub-list for extension extendee
	0, // [0:1] is the sub-list for field type_name
}

func init() { file_peering_proto_init() }
func file_peering_proto_init() {
	if File_peering_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_peering_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*Empty); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_peering_proto_msgTypes[1].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*Machine); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_peering_proto_msgTypes[2].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StartPeerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_peering_proto_msgTypes[3].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*RouteRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_peering_proto_rawDesc,
			NumEnums:      0,
			NumMessages:   4,
			NumExtensions: 0,
			NumServices:   1,
		},
		GoTypes:           file_peering_proto_goTypes,
		DependencyIndexes: file_peering_proto_depIdxs,
		MessageInfos:      file_peering_proto_msgTypes,
	}.Build()
	File_peering_proto = out.File
	file_peering_proto_rawDesc = nil
	file_peering_proto_goTypes = nil
	file_peering_proto_depIdxs = nil
}
