/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
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
	"sync"
)

type shellid int64
type id uint64

type shell struct {
	// some shell information
	planeNo uint64

	// firecracker machines
	machines map[id]*machine
	sync.RWMutex
}

type link struct {
	handle    int64
	sourceNet string
	targetNet string

	blocked     bool
	initialized bool

	latency   float64
	bandwidth uint64
}
