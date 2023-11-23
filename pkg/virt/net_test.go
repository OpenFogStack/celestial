package virt

import (
	"net"
	"reflect"
	"testing"

	"github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

func Test_getNet(t *testing.T) {
	type args struct {
		id orchestrator2.MachineID
	}
	tests := []struct {
		name    string
		args    args
		want    network
		wantErr bool
	}{
		{
			name: "test1",
			args: args{
				id: orchestrator2.MachineID{
					Group: 1,
					Id:    1,
				},
			},
			want: network{
				ip: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 6),
					Mask: net.CIDRMask(30, 32),
				},
				gateway: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 5),
					Mask: net.CIDRMask(30, 32),
				},
				network: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 4),
					Mask: net.CIDRMask(30, 32),
				},
				mac: net.HardwareAddr{
					0xAA, 0xCE, 1, 0, 0, 3,
				},
				tap: "ct-1-1",
			},
			wantErr: false,
		},
		{
			name: "test2",
			args: args{
				id: orchestrator2.MachineID{
					Group: 1,
					Id:    16385,
				},
			},
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := getNet(tt.args.id)
			if (err != nil) != tt.wantErr {
				t.Errorf("getNet() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("getNet() got = %v, want %v", got, tt.want)
			}
		})
	}
}

func Test_getID(t *testing.T) {
	type args struct {
		ip net.IP
	}
	tests := []struct {
		name    string
		args    args
		want    orchestrator2.MachineID
		wantErr bool
	}{
		{
			name: "test1",
			args: args{
				ip: net.IPv4(10, 1, 0, 6),
			},
			want: orchestrator2.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test2",
			args: args{
				ip: net.IPv4(10, 1, 0, 5),
			},
			want: orchestrator2.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test3",
			args: args{
				ip: net.IPv4(10, 1, 0, 4),
			},
			want: orchestrator2.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test4",
			args: args{
				ip: net.IPv4(10, 1, 0, 7),
			},
			want: orchestrator2.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test5",
			args: args{
				ip: net.IPv4(127, 0, 0, 1),
			},
			want:    orchestrator2.MachineID{},
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := getID(tt.args.ip)
			if (err != nil) != tt.wantErr {
				t.Errorf("getID() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("getID() got = %v, want %v", got, tt.want)
			}
		})
	}
}
