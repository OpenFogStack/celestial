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
