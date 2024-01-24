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

package netem

import "net"

type ipnet struct {
	ipA   byte
	ipB   byte
	ipC   byte
	ipD   byte
	maskA byte
	maskB byte
	maskC byte
	maskD byte
}

func (i ipnet) String() string {
	n := i.ipnet()
	return n.String()
}

func (i ipnet) ip() net.IP {
	return net.IPv4(i.ipA, i.ipB, i.ipC, i.ipD)
}

func (i ipnet) mask() net.IPMask {
	return net.IPv4Mask(i.maskA, i.maskB, i.maskC, i.maskD)
}

func (i ipnet) ipnet() net.IPNet {
	return net.IPNet{
		IP:   i.ip(),
		Mask: i.mask(),
	}
}

func fromIPNet(n net.IPNet) ipnet {
	ip := n.IP.To4()
	mask := n.Mask

	return ipnet{
		ipA:   ip[0],
		ipB:   ip[1],
		ipC:   ip[2],
		ipD:   ip[3],
		maskA: mask[0],
		maskB: mask[1],
		maskC: mask[2],
		maskD: mask[3],
	}
}
