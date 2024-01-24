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

package info

type Identifier struct {
	Shell uint8
	ID    uint32
	Name  string
}

type Node struct {
	Type       string
	Active     bool
	Identifier Identifier
}

type Shell struct {
	Sats []Node
}

type Constellation struct {
	Shells         []Shell
	Groundstations []Node
}

type Segment struct {
	Source    Identifier
	Target    Identifier
	Delay     uint32
	Bandwidth uint64
}

type Path struct {
	Source    Identifier
	Target    Identifier
	Delay     uint32
	Bandwidth uint64
	Segments  []Segment
	Blocked   bool
}
