package orchestrator2

import (
	"reflect"
	"testing"
)

/*
import (
	"bufio"
	"os"
	"reflect"
	"strconv"
	"strings"
	"testing"

	log "github.com/sirupsen/logrus"
)

func TestMain(m *testing.M) {
	log.SetLevel(log.DebugLevel)
	os.Exit(m.Run())
}

func testDistances(t *testing.T, machines []MachineID, state ISLState, want links) links {
	gotL, err := distances(machines, state)
	if err != nil {
		t.Errorf("distanceAndPredecessorMatrices() error = %v", err)
		return nil
	}

	for k, v := range gotL {
		for k1, v1 := range v {
			if v1.Blocked != want[k][k1].Blocked {
				t.Errorf("from %s to %s got blocked = %v, want %v", k.String(), k1.String(), v1.Blocked, want[k][k1].Blocked)
			}
			if v1.Latency != want[k][k1].Latency {
				t.Errorf("from %s to %s got latency = %v, want %v", k.String(), k1.String(), v1.Latency, want[k][k1].Latency)
			}
			if v1.Bandwidth != want[k][k1].Bandwidth {
				t.Errorf("from %s to %s got bandwidth = %v, want %v", k.String(), k1.String(), v1.Bandwidth, want[k][k1].Bandwidth)
			}
		}
	}

	if !reflect.DeepEqual(gotL, want) {
		t.Errorf("distanceAndPredecessorMatrices() gotL = %v, want %v", gotL, want)
	}

	return gotL
}

func testPath(t *testing.T, got links, wantL links, wantP map[MachineID]map[MachineID]PathInfo) {
	for source := range wantP {
		for target := range wantP[source] {

			wantErr := wantL[source][target].Blocked || source == target

			gotPaths, err := path(source, target, got)

			if wantErr {
				if err == nil {
					t.Errorf("from %s to %s got no error, want error", source.String(), target.String())
				}
				continue
			}

			if err != nil {
				t.Errorf("paths() error = %v", err)
				return
			}

			if gotPaths.Source != source {
				t.Errorf("from %s to %s got source = %v, want %v", source.String(), target.String(), gotPaths.Source, source)
			}

			if gotPaths.Target != target {
				t.Errorf("from %s to %s got target = %v, want %v", source.String(), target.String(), gotPaths.Target, target)
			}

			if gotPaths.Latency != wantP[source][target].Latency {
				t.Errorf("from %s to %s got delay = %v, want %v", source.String(), target.String(), gotPaths.Latency, wantP[source][target].Latency)
			}

			if gotPaths.Bandwidth != wantP[source][target].Bandwidth {
				t.Errorf("from %s to %s got bandwidth = %v, want %v", source.String(), target.String(), gotPaths.Bandwidth, wantP[source][target].Bandwidth)
			}

			if len(gotPaths.Segments) != len(wantP[source][target].Segments) {
				t.Errorf("from %s to %s got segments = %v, want %v", source.String(), target.String(), gotPaths.Segments, wantP[source][target].Segments)
			}

			for s := range gotPaths.Segments {
				if gotPaths.Segments[s].Source != wantP[source][target].Segments[s].Source {
					t.Errorf("from %s to %s got source = %v, want %v", source.String(), target.String(), gotPaths.Segments[s].Source, wantP[source][target].Segments[s].Source)
				}

				if gotPaths.Segments[s].Target != wantP[source][target].Segments[s].Target {
					t.Errorf("from %s to %s got target = %v, want %v", source.String(), target.String(), gotPaths.Segments[s].Target, wantP[source][target].Segments[s].Target)
				}

				if gotPaths.Segments[s].Latency != wantP[source][target].Segments[s].Latency {
					t.Errorf("from %s to %s got delay = %v, want %v", source.String(), target.String(), gotPaths.Segments[s].Latency, wantP[source][target].Segments[s].Latency)
				}

				if gotPaths.Segments[s].Bandwidth != wantP[source][target].Segments[s].Bandwidth {
					t.Errorf("from %s to %s got bandwidth = %v, want %v", source.String(), target.String(), gotPaths.Segments[s].Bandwidth, wantP[source][target].Segments[s].Bandwidth)
				}
			}
		}
	}
}

func Benchmark_distancesSmall(b *testing.B) {
	testDir := "tests/"

	// get all the .graph files, parse corresponding .dist and .pred files, execute tests
	graphFile := "small.graph"
	machines, s, err := parseGraphFile(testDir + graphFile)
	if err != nil {
		b.Errorf("parseGraphFile() error = %v", err)
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = distances(machines, s)
	}
}

func Benchmark_distancesMedium(b *testing.B) {
	testDir := "tests/"

	// get all the .graph files, parse corresponding .dist and .pred files, execute tests
	graphFile := "topology5.graph"
	machines, s, err := parseGraphFile(testDir + graphFile)
	if err != nil {
		b.Errorf("parseGraphFile() error = %v", err)
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = distances(machines, s)
	}
}

func Benchmark_distancesLarge(b *testing.B) {
	testDir := "tests/"

	// get all the .graph files, parse corresponding .dist and .pred files, execute tests
	graphFile := "topology50.graph"
	machines, s, err := parseGraphFile(testDir + graphFile)
	if err != nil {
		b.Errorf("parseGraphFile() error = %v", err)
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = distances(machines, s)
	}
}

func Benchmark_pathLarge(b *testing.B) {
	testDir := "tests/"

	// get all the .graph files, parse corresponding .dist and .pred files, execute tests
	graphFile := "topology50.graph"
	machines, s, err := parseGraphFile(testDir + graphFile)
	if err != nil {
		b.Errorf("parseGraphFile() error = %v", err)
		return
	}

	l, err := distances(machines, s)
	if err != nil {
		b.Errorf("parseGraphFile() error = %v", err)
		return
	}

	i := MachineID{Id: 0}
	j := MachineID{Id: 1250}

	b.ResetTimer()
	for k := 0; k < b.N; k++ {
		_, _ = path(i, j, l)
	}
}

func Test_distancesAndPath(t *testing.T) {
	testDir := "tests/"

	// get all the .graph files, parse corresponding .dist and .pred files, execute tests
	//for _, graphFile := range []string{"small.graph", "topology5.graph", "topology70.graph"} {
	graphFile := "topology50.graph"
	solution := graphFile[:len(graphFile)-len(".graph")] + ".solution"

	machines, s, err := parseGraphFile(testDir + graphFile)
	if err != nil {
		t.Errorf("parseGraphFile() error = %v", err)
		return
	}

	wantL, wantP, err := parseSolutionFile(testDir + solution)
	if err != nil {
		t.Errorf("parseDistFile() error = %v", err)
		return
	}

	gotL := testDistances(t, machines, s, wantL)
	testPath(t, gotL, wantL, wantP)
	//}
}

func parseSolutionFile(name string) (links, map[MachineID]map[MachineID]PathInfo, error) {
	l := make(links)
	pathinfos := make(map[MachineID]map[MachineID]PathInfo)

	file, err := os.Open(name)
	if err != nil {
		return nil, nil, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if !strings.HasPrefix(line, "link=") {
			continue
		}

		parts := strings.Split(strings.Split(line, "=")[1], ",")
		id1, err := strconv.Atoi(parts[0])
		// convert to uint32
		if err != nil {
			return nil, nil, err
		}
		id2, err := strconv.Atoi(parts[1])
		// convert to uint32
		if err != nil {
			return nil, nil, err
		}

		if id1 == id2 {
			continue
		}

		link := &Link{}

		if parts[2] == "inf" {
			link.Blocked = true
		} else {
			link.Blocked = false
			latency, err := strconv.Atoi(parts[2])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}
			link.Latency = uint32(latency)

			bandwidth, err := strconv.Atoi(parts[3])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}

			link.Bandwidth = uint64(bandwidth)
		}

		if _, ok := l[MachineID{Id: uint32(id1)}]; !ok {
			l[MachineID{Id: uint32(id1)}] = make(map[MachineID]*Link)
		}

		l[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}] = link
	}

	// scan everything again, this time for paths
	file.Seek(0, 0)
	scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		parts := strings.Split(strings.Split(line, "=")[1], ",")
		id1, err := strconv.Atoi(parts[0])
		// convert to uint32
		if err != nil {
			return nil, nil, err
		}
		id2, err := strconv.Atoi(parts[1])
		// convert to uint32
		if err != nil {
			return nil, nil, err
		}

		if parts[2] == "inf" {
			// no need for path on a blocked link
			continue
		}

		p := strings.Split(parts[4], "|")

		if len(p) == 1 {
			continue
		}

		pi := PathInfo{
			Source:    MachineID{Id: uint32(id1)},
			Target:    MachineID{Id: uint32(id2)},
			Latency:   l[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}].Latency,
			Bandwidth: l[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}].Bandwidth,
			Segments:  make([]SegmentInfo, 0),
		}

		a := id1
		for i := 1; i < len(p); i++ {
			b, err := strconv.Atoi(p[i])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}

			s := SegmentInfo{
				Source:    MachineID{Id: uint32(a)},
				Target:    MachineID{Id: uint32(b)},
				Latency:   l[MachineID{Id: uint32(a)}][MachineID{Id: uint32(b)}].Latency,
				Bandwidth: l[MachineID{Id: uint32(a)}][MachineID{Id: uint32(b)}].Bandwidth,
			}

			pi.Segments = append(pi.Segments, s)
			a = b
		}

		l[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}].next = pi.Segments[0].Target

		if _, ok := pathinfos[MachineID{Id: uint32(id1)}]; !ok {
			pathinfos[MachineID{Id: uint32(id1)}] = make(map[MachineID]PathInfo)
		}

		pathinfos[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}] = pi
	}

	return l, pathinfos, nil
}

func parseGraphFile(name string) ([]MachineID, ISLState, error) {
	m := make([]MachineID, 0)
	s := make(ISLState)

	file, err := os.Open(name)
	if err != nil {
		return nil, nil, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		l := strings.TrimSpace(scanner.Text())
		// node=X means add a node X
		if strings.HasPrefix(l, "node=") {
			id, err := strconv.Atoi(strings.Split(l, "=")[1])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}

			m = append(m, MachineID{Id: uint32(id)})

			continue
		}

		// link=X,Y,delay,bandwidth means add an ISL
		if strings.HasPrefix(l, "link=") {
			parts := strings.Split(strings.Split(l, "=")[1], ",")
			id1, err := strconv.Atoi(parts[0])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}
			id2, err := strconv.Atoi(parts[1])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}
			latency, err := strconv.Atoi(parts[2])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}
			bandwidth, err := strconv.Atoi(parts[3])
			// convert to uint32
			if err != nil {
				return nil, nil, err
			}

			if _, ok := s[MachineID{Id: uint32(id1)}]; !ok {
				s[MachineID{Id: uint32(id1)}] = make(map[MachineID]*ISL)
			}

			s[MachineID{Id: uint32(id1)}][MachineID{Id: uint32(id2)}] = &ISL{
				Latency:   uint32(latency),
				Bandwidth: uint64(bandwidth),
			}
			continue
		}
	}

	return m, s, nil
}

*/

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
		// TODO: Add test cases.
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
