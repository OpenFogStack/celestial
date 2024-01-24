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

package netem

import (
	"net"
	"testing"
)

func Test_getBaseNet(t *testing.T) {
	type args struct {
		ipNet net.IPNet
	}
	tests := []struct {
		name string
		args args
		want *net.IPNet
	}{
		{
			name: "test1",
			args: args{
				ipNet: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 0),
					Mask: net.IPv4Mask(255, 255, 255, 0),
				},
			},
			want: &net.IPNet{
				IP:   net.IPv4(10, 1, 0, 0),
				Mask: net.IPv4Mask(255, 255, 255, 0),
			},
		},
		{
			name: "test2",
			args: args{
				ipNet: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 1),
					Mask: net.IPv4Mask(255, 255, 255, 0),
				},
			},
			want: &net.IPNet{
				IP:   net.IPv4(10, 1, 0, 0),
				Mask: net.IPv4Mask(255, 255, 255, 0),
			},
		},
		{
			name: "test3",
			args: args{
				ipNet: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 2),
					Mask: net.IPv4Mask(255, 255, 255, 0),
				},
			},
			want: &net.IPNet{
				IP:   net.IPv4(10, 1, 0, 0),
				Mask: net.IPv4Mask(255, 255, 255, 0),
			},
		},
		{
			name: "test4",
			args: args{
				ipNet: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 3),
					Mask: net.IPv4Mask(255, 255, 255, 0),
				},
			},
			want: &net.IPNet{
				IP:   net.IPv4(10, 1, 0, 0),
				Mask: net.IPv4Mask(255, 255, 255, 0),
			},
		},
		{
			name: "test5",
			args: args{
				ipNet: net.IPNet{
					IP:   net.IPv4(10, 1, 0, 4),
					Mask: net.IPv4Mask(255, 255, 255, 252),
				},
			},
			want: &net.IPNet{
				IP:   net.IPv4(10, 1, 0, 4),
				Mask: net.IPv4Mask(255, 255, 255, 252),
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := getBaseNet(tt.args.ipNet); got.String() != tt.want.String() {
				t.Errorf("getBaseNet() = %v, want %v", got, tt.want)
			}
		})
	}
}
