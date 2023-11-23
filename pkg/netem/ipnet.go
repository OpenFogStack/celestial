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
