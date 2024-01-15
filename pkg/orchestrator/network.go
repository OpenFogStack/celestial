package orchestrator

import (
	"fmt"
	"sort"
	"strings"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

func (n NetworkState) String() string {
	s := make([]string, 0)

	for i := range n {
		for j := range n[i] {
			s = append(s, fmt.Sprintf("%s -> %s : %s", i.String(), j.String(), n[i][j].String()))
		}
	}

	// sort
	sort.Strings(s)

	return strings.Join(s, "\n")
}

func (l Link) String() string {
	if l.Blocked {
		return "blocked"
	}

	return fmt.Sprintf("%dus %dbps (next: %s)", l.Latency, l.Bandwidth, l.Next.String())
}

func path(a, b MachineID, n NetworkState) (PathInfo, error) {
	if a == b {
		return PathInfo{}, errors.Errorf("cannot give path from %s to itself", a)
	}

	log.Debugf("path from %s to %s", a.String(), b.String())

	if b.lt(a) {
		return path(b, a, n)
	}

	p := PathInfo{
		Source: a,
		Target: b,
	}

	if n[a][b].Blocked {
		log.Debugf("path from %s to %s is blocked", a.String(), b.String())
		p.Blocked = true
		return p, nil
	}

	p.Latency = n[a][b].Latency
	p.Bandwidth = n[a][b].Bandwidth
	p.Segments = make([]SegmentInfo, 0)

	for a != b {
		x, y := a, b
		if y.lt(x) {
			x, y = y, x
		}

		hop := n[x][y]

		log.Debugf("path from %s to %s: %s", a.String(), b.String(), hop.String())
		s := SegmentInfo{
			Source:    x,
			Target:    hop.Next,
			Latency:   n[x][hop.Next].Latency,
			Bandwidth: n[x][hop.Next].Bandwidth,
		}

		// weird prepend action
		//p.Segments = append([]SegmentInfo{s}, p.Segments...)
		p.Segments = append(p.Segments, s)

		a = hop.Next
		b = y
	}

	return p, nil
}

/*
// consider: technically, we allow paths to go through a ground station. Decide if this makes sense...
func distances(machines []MachineID, state ISLState) (links, error) {
	t := time.Now()

	type distance struct {
		latency   uint32
		bandwidth uint64
	}

	// generate a matrix
	dist := make([][]distance, len(machines))
	// next hop graph
	next := make([][]int, len(machines))

	for i := range dist {
		dist[i] = make([]distance, len(machines))
		for j := range dist[i] {
			dist[i][j] = distance{latency: ^uint32(0)}
		}

		next[i] = make([]int, len(machines))
		for j := range next[i] {
			next[i][j] = -1
		}
	}

	id := make(map[MachineID]int)

	for i, m := range machines {
		id[m] = i
	}

	for a := range state {
		for b := range state[a] {
			dist[id[a]][id[b]].latency = state[a][b].Latency
			dist[id[a]][id[b]].bandwidth = state[a][b].Bandwidth
			next[id[a]][id[b]] = id[b]
		}
	}

	for a := range machines {
		dist[a][a].latency = 0
		dist[a][a].bandwidth = ^uint64(0)
		// not adding itself to matrix
		// only reason is compatibility with scipy implementation
		//pred[a][a] = a
	}

	// floyd-warshall
	for k := range dist {
		for i := range dist {
			for j := range dist {
				if dist[i][k].latency == ^uint32(0) || dist[k][j].latency == ^uint32(0) {
					continue
				}
				if dist[i][j].latency > dist[i][k].latency+dist[k][j].latency {
					dist[i][j].latency = dist[i][k].latency + dist[k][j].latency
					dist[i][j].bandwidth = min(dist[i][k].bandwidth, dist[k][j].bandwidth)

					next[i][j] = next[i][k]
				}
			}
		}
	}

	log.Debugf("fw took %s", time.Since(t))

	l := make(links)

	for i := range dist {
		for j := range dist {
			if i == j {
				continue
			}

			if _, ok := l[machines[i]]; !ok {
				l[machines[i]] = make(map[MachineID]*Link)
			}

			if dist[i][j].latency == ^uint32(0) {
				l[machines[i]][machines[j]] = &Link{
					Blocked: true,
				}
				// no need for path matrix entry if link is blocked
				continue
			}

			l[machines[i]][machines[j]] = &Link{
				Latency:   dist[i][j].latency,
				Bandwidth: dist[i][j].bandwidth,
				Blocked:   false,
				next:      machines[next[i][j]],
			}
		}
	}

	log.Debugf("distances took %s", time.Since(t))

	return l, nil
}
*/
