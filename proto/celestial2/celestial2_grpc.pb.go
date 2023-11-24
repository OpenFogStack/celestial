// Code generated by protoc-gen-go-grpc. DO NOT EDIT.
// versions:
// - protoc-gen-go-grpc v1.2.0
// - protoc             v4.25.0
// source: celestial2.proto

package celestial2

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

// CelestialClient is the client API for Celestial service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type CelestialClient interface {
	Register(ctx context.Context, in *RegisterRequest, opts ...grpc.CallOption) (*RegisterResponse, error)
	Init(ctx context.Context, in *InitRequest, opts ...grpc.CallOption) (*Empty, error)
	Update(ctx context.Context, in *UpdateRequest, opts ...grpc.CallOption) (*Empty, error)
	Stop(ctx context.Context, in *Empty, opts ...grpc.CallOption) (*Empty, error)
}

type celestialClient struct {
	cc grpc.ClientConnInterface
}

func NewCelestialClient(cc grpc.ClientConnInterface) CelestialClient {
	return &celestialClient{cc}
}

func (c *celestialClient) Register(ctx context.Context, in *RegisterRequest, opts ...grpc.CallOption) (*RegisterResponse, error) {
	out := new(RegisterResponse)
	err := c.cc.Invoke(ctx, "/openfogstack.celestial.celestial2.Celestial/Register", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *celestialClient) Init(ctx context.Context, in *InitRequest, opts ...grpc.CallOption) (*Empty, error) {
	out := new(Empty)
	err := c.cc.Invoke(ctx, "/openfogstack.celestial.celestial2.Celestial/Init", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *celestialClient) Update(ctx context.Context, in *UpdateRequest, opts ...grpc.CallOption) (*Empty, error) {
	out := new(Empty)
	err := c.cc.Invoke(ctx, "/openfogstack.celestial.celestial2.Celestial/Update", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *celestialClient) Stop(ctx context.Context, in *Empty, opts ...grpc.CallOption) (*Empty, error) {
	out := new(Empty)
	err := c.cc.Invoke(ctx, "/openfogstack.celestial.celestial2.Celestial/Stop", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// CelestialServer is the server API for Celestial service.
// All implementations should embed UnimplementedCelestialServer
// for forward compatibility
type CelestialServer interface {
	Register(context.Context, *RegisterRequest) (*RegisterResponse, error)
	Init(context.Context, *InitRequest) (*Empty, error)
	Update(context.Context, *UpdateRequest) (*Empty, error)
	Stop(context.Context, *Empty) (*Empty, error)
}

// UnimplementedCelestialServer should be embedded to have forward compatible implementations.
type UnimplementedCelestialServer struct {
}

func (UnimplementedCelestialServer) Register(context.Context, *RegisterRequest) (*RegisterResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Register not implemented")
}
func (UnimplementedCelestialServer) Init(context.Context, *InitRequest) (*Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Init not implemented")
}
func (UnimplementedCelestialServer) Update(context.Context, *UpdateRequest) (*Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Update not implemented")
}
func (UnimplementedCelestialServer) Stop(context.Context, *Empty) (*Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Stop not implemented")
}

// UnsafeCelestialServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to CelestialServer will
// result in compilation errors.
type UnsafeCelestialServer interface {
	mustEmbedUnimplementedCelestialServer()
}

func RegisterCelestialServer(s grpc.ServiceRegistrar, srv CelestialServer) {
	s.RegisterService(&Celestial_ServiceDesc, srv)
}

func _Celestial_Register_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(RegisterRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(CelestialServer).Register(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/openfogstack.celestial.celestial2.Celestial/Register",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(CelestialServer).Register(ctx, req.(*RegisterRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Celestial_Init_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(InitRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(CelestialServer).Init(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/openfogstack.celestial.celestial2.Celestial/Init",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(CelestialServer).Init(ctx, req.(*InitRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Celestial_Update_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(UpdateRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(CelestialServer).Update(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/openfogstack.celestial.celestial2.Celestial/Update",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(CelestialServer).Update(ctx, req.(*UpdateRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Celestial_Stop_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(Empty)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(CelestialServer).Stop(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/openfogstack.celestial.celestial2.Celestial/Stop",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(CelestialServer).Stop(ctx, req.(*Empty))
	}
	return interceptor(ctx, in, info, handler)
}

// Celestial_ServiceDesc is the grpc.ServiceDesc for Celestial service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var Celestial_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "openfogstack.celestial.celestial2.Celestial",
	HandlerType: (*CelestialServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Register",
			Handler:    _Celestial_Register_Handler,
		},
		{
			MethodName: "Init",
			Handler:    _Celestial_Init_Handler,
		},
		{
			MethodName: "Update",
			Handler:    _Celestial_Update_Handler,
		},
		{
			MethodName: "Stop",
			Handler:    _Celestial_Stop_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "celestial2.proto",
}
