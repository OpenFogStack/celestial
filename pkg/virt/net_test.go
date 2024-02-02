/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, version 3.
*
* This program is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
**/

package virt

import (
	"net"
	"reflect"
	"testing"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

func Test_getNet(t *testing.T) {
	type args struct {
		id orchestrator.MachineID
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
				id: orchestrator.MachineID{
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
					0xAA, 0xCE, 0x1, 0, 0, 0x3,
				},
				tap: "ct-1-1",
			},
			wantErr: false,
		},
		{
			name: "test2",
			args: args{
				id: orchestrator.MachineID{
					Group: 1,
					Id:    16385,
				},
			},
			wantErr: true,
		},
		{
			name: "test3",
			args: args{
				id: orchestrator.MachineID{
					Group: 4,
					Id:    17,
				},
			},
			want: network{
				ip: net.IPNet{
					IP:   net.IPv4(10, 4, 0, 70),
					Mask: net.CIDRMask(30, 32),
				},
				gateway: net.IPNet{
					IP:   net.IPv4(10, 4, 0, 69),
					Mask: net.CIDRMask(30, 32),
				},
				network: net.IPNet{
					IP:   net.IPv4(10, 4, 0, 68),
					Mask: net.CIDRMask(30, 32),
				},
				mac: net.HardwareAddr{
					0xAA, 0xCE, 0x4, 0, 0, 0x13,
				},
				tap: "ct-4-17",
			},
			wantErr: false,
		},
		{
			name: "test4",
			args: args{
				id: orchestrator.MachineID{
					Group: 1,
					Id:    1385,
				},
			},
			want: network{
				ip: net.IPNet{
					IP:   net.IPv4(10, 1, 21, 166),
					Mask: net.CIDRMask(30, 32),
				},
				gateway: net.IPNet{
					IP:   net.IPv4(10, 1, 21, 165),
					Mask: net.CIDRMask(30, 32),
				},
				network: net.IPNet{
					IP:   net.IPv4(10, 1, 21, 164),
					Mask: net.CIDRMask(30, 32),
				},
				mac: net.HardwareAddr{
					0xAA, 0xCE, 0x4, 0, 0, 0x13,
				},
				tap: "ct-1-1385",
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := getNet(tt.args.id)
			if (err != nil) != tt.wantErr {
				t.Errorf("getNet() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got.ip.String() != tt.want.ip.String() {
				t.Errorf("getNet() got ip = %v, want ip %v", got.ip, tt.want.ip)
			}
			if got.gateway.String() != tt.want.gateway.String() {
				t.Errorf("getNet() got gateway = %v, want gateway %v", got.gateway, tt.want.gateway)
			}
			if got.network.String() != tt.want.network.String() {
				t.Errorf("getNet() got network = %v, want network %v", got.network, tt.want.network)
			}
			if got.mac.String() != tt.want.mac.String() {
				t.Errorf("getNet() got mac = %v, want mac %v", got.mac, tt.want.mac)
			}
			if !reflect.DeepEqual(got.tap, tt.want.tap) {
				t.Errorf("getNet() got tap = %v, want tap %v", got.tap, tt.want.tap)
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
		want    orchestrator.MachineID
		wantErr bool
	}{
		{
			name: "test1",
			args: args{
				ip: net.IPv4(10, 1, 0, 6),
			},
			want: orchestrator.MachineID{
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
			want: orchestrator.MachineID{
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
			want: orchestrator.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test4",
			args: args{
				ip: net.IPv4(10, 1, 0, 2),
			},
			want: orchestrator.MachineID{
				Group: 1,
				Id:    0,
			},
			wantErr: false,
		},
		{
			name: "test5",
			args: args{
				ip: net.IPv4(10, 1, 0, 7),
			},
			want: orchestrator.MachineID{
				Group: 1,
				Id:    1,
			},
			wantErr: false,
		},
		{
			name: "test6",
			args: args{
				ip: net.IPv4(127, 0, 0, 1),
			},
			want:    orchestrator.MachineID{},
			wantErr: true,
		},
		{
			name: "test7",
			args: args{
				ip: net.IPv6zero,
			},
			want:    orchestrator.MachineID{},
			wantErr: true,
		},
		{
			name: "test8",
			args: args{
				ip: net.IPv4(10, 1, 0, 0),
			},
			want: orchestrator.MachineID{
				Group: 1,
				Id:    0,
			},
			wantErr: false,
		},
		{
			name: "test9",
			args: args{
				ip: net.IPv4(10, 1, 21, 166),
			},
			want: orchestrator.MachineID{
				Group: 1,
				Id:    1385,
			},
			wantErr: false,
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
