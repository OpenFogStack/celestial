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
}

// GroundStation is returned by `/gst/{name}`
type GroundStation struct {
	Identifier Identifier `json:"identifier"`
	Name       string     `json:"name"`
	Lat        float64    `json:"lat"`
	Lon        float64    `json:"lon"`
}

// Sat is returned by `/self` and `/shell/{group}/{id}`.
type Sat struct {
	Identifier Identifier `json:"identifier"`
	Active     bool       `json:"active"`
	TLE1       string     `json:"tle1"`
	TLE2       string     `json:"tle2"`
}

// Shell is returned by `/shell/{group}`.
type Shell struct {
	Sats []Sat `json:"sats"`
}

// Constellation is returned by `/info`.
type Constellation struct {
	Shells         []Shell         `json:"shells"`
	GroundStations []GroundStation `json:"ground_stations"`
}

type Segment struct {
	Source    Identifier `json:"source"`
	Target    Identifier `json:"target"`
	Delay     uint32     `json:"delay,omitempty"`
	Bandwidth uint64     `json:"bandwidth,omitempty"`
}

// Path is returned by `/path/{source_group}/{source_id}/{target_group}/{target_id}`.
type Path struct {
	Source    Identifier `json:"source"`
	Target    Identifier `json:"target"`
	Delay     uint32     `json:"delay,omitempty"`
	Bandwidth uint64     `json:"bandwidth,omitempty"`
	Blocked   bool       `json:"blocked,omitempty"`
	Segments  []Segment  `json:"segments"`
}
