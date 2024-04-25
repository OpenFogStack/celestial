//go:build linux && amd64
// +build linux,amd64

/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2024 Soeren Becker, Nils Japke, Tobias Pfandzelter, The
* OpenFogStack Team.
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

package ebpfem

import (
	"sync"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

const (
	DEFAULT_LATENCY_US     = 0
	DEFAULT_BANDWIDTH_KBPS = 1_000_000

	BLOCKED_LATENCY_US     = 1_000_000_000
	BLOCKED_BANDWIDTH_KBPS = 0
)

type handleKbpsDelay struct {
	throttleRateKbps uint32
	delayUs          uint32
}

type vm struct {
	netIf string

	// ebpf specific
	objs *edtObjects
	hbd  map[string]*handleKbpsDelay

	sync.Mutex
}

type EBPFem struct {
	vms map[orchestrator.MachineID]*vm
	sync.RWMutex
}
