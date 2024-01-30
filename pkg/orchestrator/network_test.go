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

package orchestrator

import (
	"reflect"
	"testing"
)

func Test_path(t *testing.T) {
	type args struct {
		a MachineID
		b MachineID
		n NetworkState
	}
	tests := []struct {
		name    string
		args    args
		want    PathInfo
		wantErr bool
	}{
		{
			name: "test1",
			args: args{
				a: MachineID{Id: 1},
				b: MachineID{Id: 0},
				n: NetworkState{
					MachineID{Id: 0}: {
						MachineID{Id: 1}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 1,
							},
						},
					},
					MachineID{Id: 1}: {
						MachineID{Id: 0}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 0,
							},
						},
					},
				},
			},
			want: PathInfo{
				Source:    MachineID{Id: 1},
				Target:    MachineID{Id: 0},
				Latency:   1,
				Bandwidth: 1,
				Segments: []SegmentInfo{
					{
						Source:    MachineID{Id: 0},
						Target:    MachineID{Id: 1},
						Latency:   1,
						Bandwidth: 1,
					},
				},
				Blocked: false,
			},
			wantErr: false,
		}, {
			name: "test1",
			args: args{
				a: MachineID{Id: 0},
				b: MachineID{Id: 1},
				n: NetworkState{
					MachineID{Id: 0}: {
						MachineID{Id: 1}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 1,
							},
						},
					},
					MachineID{Id: 1}: {
						MachineID{Id: 0}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 0,
							},
						},
					},
				},
			},
			want: PathInfo{
				Source:    MachineID{Id: 0},
				Target:    MachineID{Id: 1},
				Latency:   1,
				Bandwidth: 1,
				Segments: []SegmentInfo{
					{
						Source:    MachineID{Id: 0},
						Target:    MachineID{Id: 1},
						Latency:   1,
						Bandwidth: 1,
					},
				},
				Blocked: false,
			},
			wantErr: false,
		}, {
			name: "test2",
			args: args{
				a: MachineID{Id: 1},
				b: MachineID{Id: 0},
				n: NetworkState{
					MachineID{Id: 0}: {
						MachineID{Id: 1}: &Link{
							Blocked:   false,
							Latency:   2,
							Bandwidth: 1,
							Next: MachineID{
								Id: 2,
							},
						},
						MachineID{Id: 2}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 2,
							},
						},
					},
					MachineID{Id: 1}: {
						MachineID{Id: 0}: &Link{
							Blocked:   false,
							Latency:   2,
							Bandwidth: 1,
							Next: MachineID{
								Id: 2,
							},
						},
						MachineID{Id: 2}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 2,
							},
						},
					},
					MachineID{Id: 2}: {
						MachineID{Id: 0}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 0,
							},
						},
						MachineID{Id: 1}: &Link{
							Blocked:   false,
							Latency:   1,
							Bandwidth: 1,
							Next: MachineID{
								Id: 1,
							},
						},
					},
				},
			},
			want: PathInfo{
				Source:    MachineID{Id: 1},
				Target:    MachineID{Id: 0},
				Latency:   2,
				Bandwidth: 1,
				Segments: []SegmentInfo{
					{
						Source:    MachineID{Id: 1},
						Target:    MachineID{Id: 2},
						Latency:   1,
						Bandwidth: 1,
					}, {
						Source:    MachineID{Id: 2},
						Target:    MachineID{Id: 0},
						Latency:   1,
						Bandwidth: 1,
					},
				},
				Blocked: false,
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := path(tt.args.a, tt.args.b, tt.args.n)
			if (err != nil) != tt.wantErr {
				t.Errorf("path() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("path() got = %v, want %v", got, tt.want)
			}
		})
	}
}
