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
	Shell uint8  `json:"shell"`
	ID    uint32 `json:"id"`
	Name  string `json:"name,omitempty"`
}

// Node is returned by `/self`, `/gst/{name}` and `/shell/{group}/{id}`.
type Node struct {
	Type       string     `json:"type"`
	Active     bool       `json:"active"`
	Identifier Identifier `json:"identifier"`
}

// Shell is returned by `/shell/{group}`.
type Shell struct {
	Sats []Node `json:"sats"`
}

// Constellation is returned by `/info`.
type Constellation struct {
	Shells         []Shell `json:"shells"`
	Groundstations []Node  `json:"groundstations"`
}

type Segment struct {
	Source        Identifier `json:"source"`
	Target        Identifier `json:"target"`
	DelayUs       uint32     `json:"delay_us,omitempty"`
	BandwidthKbps uint64     `json:"bandwidth_kbps,omitempty"`
}

// Path is returned by `/path/{source_group}/{source_id}/{target_group}/{target_id}`.
type Path struct {
	Source        Identifier `json:"source"`
	Target        Identifier `json:"target"`
	DelayUs       uint32     `json:"delay_us,omitempty"`
	BandwidthKbps uint64     `json:"bandwidth_kbits,omitempty"`
	Blocked       bool       `json:"blocked,omitempty"`
	Segments      []Segment  `json:"segments"`
}
