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
	"fmt"
	"sort"
	"strings"

	"github.com/pkg/errors"
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

	//log.Debugf("path from %s to %s", a.String(), b.String())

	if b.lt(a) {
		return path(b, a, n)
	}

	p := PathInfo{
		Source: a,
		Target: b,
	}

	if n[a][b].Blocked {
		//log.Debugf("path from %s to %s is blocked", a.String(), b.String())
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

		//log.Debugf("path from %s to %s: %s", a.String(), b.String(), hop.String())
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
