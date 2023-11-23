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
	"context"
	"net"
	"os"
	"os/exec"
	"strconv"

	"github.com/go-ping/ping"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
	"google.golang.org/grpc"

	"github.com/OpenFogStack/celestial/pkg/commons"
	"github.com/OpenFogStack/celestial/proto/peering"
)

type host struct {
	directAddr  net.IP
	port        uint64
	grpcPort    string
	wgAddr      net.IP
	allowedNets []*net.IPNet
	publickey   string
	latency     float64
}

func initPeering(wgaddr string) (string, error) {
	// set up wireguard
	if _, err := exec.LookPath("wg"); err != nil {
		return "", errors.Errorf("could not find wireguard on this machine: %s", err.Error())
	}

	// remove old stuff first
	err := removeWG(true)

	if err != nil {
		return "", errors.WithStack(err)
	}

	log.Debugf("Removed old wg interface")

	keyPath := "/celestial/privatekey"

	// wg genkey

	k, err := wgtypes.GeneratePrivateKey()

	if err != nil {
		return "", errors.WithStack(err)
	}

	privatekey := k.String()

	privateKeyFile, err := os.Create(keyPath)

	if err != nil {
		return "", errors.WithStack(err)
	}

	defer func(privateKeyFile *os.File) {
		err := privateKeyFile.Close()
		if err != nil {
			log.Error(err.Error())
		}
	}(privateKeyFile)

	if _, err := privateKeyFile.WriteString(privatekey); err != nil {
		return "", errors.WithStack(err)
	}

	p := k.PublicKey()
	pubkey := p.String()

	log.Debugf("Private key: %s Public key %s", privatekey, pubkey)

	// ip link add [WGINTERFACE] type wireguard
	cmd := exec.Command("ip", "link", "add", WGINTERFACE, "type", "wireguard")

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip addr add [OWN_WG_ADDRESS] dev [WGINTERFACE]
	cmd = exec.Command("ip", "addr", "add", wgaddr+MASK, "dev", WGINTERFACE)

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// wg set [WGINTERFACE] private-key [PRIVATE_KEY_FILE] listen-port [WG_PORT]
	cmd = exec.Command("wg", "set", WGINTERFACE, "private-key", keyPath, "listen-port", strconv.Itoa(WGPORT))

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip link set [WGINTERFACE] up
	cmd = exec.Command("ip", "link", "set", WGINTERFACE, "up")

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return pubkey, nil
}

func removeWG(allowFail bool) error {
	// ip link del [WGINTERFACE]
	cmd := exec.Command("ip", "link", "del", WGINTERFACE)

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func getWGAddr(index uint64) (net.IP, error) {
	if index > 253 {
		return nil, errors.Errorf("index %d is larger than allowed 253", index)
	}

	// put into subnet 192.168.50.0/24
	return net.IPv4(0xC0, 0xA8, 0x32, byte(0x02+index)), nil
}

func (o *Orchestrator) SetPeerID(id uint64) error {
	wgAddr, err := getWGAddr(id)

	if err != nil {
		return errors.WithStack(err)
	}

	o.ownHost = &host{
		wgAddr: wgAddr,
	}

	o.ownID = id

	o.ownHost.publickey, err = initPeering(o.ownHost.wgAddr.String())

	if err != nil {
		return errors.WithStack(err)
	}

	log.Debugf("Peering initialized: ID %d, public key %s", o.ownID, o.ownHost.publickey)

	return nil
}

func (o *Orchestrator) InitRemotes(addr []string) error {
	// get remotes
	for i, a := range addr {
		log.Debugf("adding remote %d with address %s", i, a)

		if uint64(i) == o.ownID {
			continue
		}

		wgAddr, err := getWGAddr(uint64(i))

		if err != nil {
			return errors.WithStack(err)
		}

		addr, port, err := net.SplitHostPort(a)

		if err != nil {
			return errors.WithStack(err)
		}

		o.remoteHosts[uint64(i)] = &host{
			directAddr:  net.ParseIP(addr),
			grpcPort:    port,
			wgAddr:      wgAddr,
			allowedNets: []*net.IPNet{},
			port:        WGPORT,
		}
	}

	return nil
}

func (o *Orchestrator) StartPeering() error {
	// send our public key to these remotes
	for _, host := range o.remoteHosts {
		conn, err := grpc.Dial(net.JoinHostPort(host.directAddr.String(), host.grpcPort), grpc.WithInsecure())

		if err != nil {
			return errors.WithStack(err)
		}

		_, err = peering.NewPeeringClient(conn).StartPeer(context.Background(), &peering.StartPeerRequest{
			Publickey: o.ownHost.publickey,
			Index:     o.ownID,
		})

		if err != nil {
			return errors.WithStack(err)
		}
	}

	return nil
}

// StartPeer starts connection to a peer
func (o *Orchestrator) StartPeer(publickey string, peer uint64) error {
	// add this peer

	p, ok := o.remoteHosts[peer]

	if !ok {
		return errors.Errorf("peer %d not known", peer)
	}

	p.publickey = publickey

	// wg set [WGINTERFACE] peer [PEER_PUBLICKEY] allowed-ips [PEER_WG_ADDR]/32 endpoint [PEER_DIRECT_ADDR]:[WGPORT]
	cmd := exec.Command("wg", "set", WGINTERFACE, "peer", p.publickey, "allowed-ips", p.wgAddr.String()+"/32", "endpoint", net.JoinHostPort(p.directAddr.String(), strconv.Itoa(WGPORT)))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// test latency to this peer
	pinger, err := ping.NewPinger(p.directAddr.String())

	if err != nil {
		return errors.WithStack(err)
	}

	pinger.SetPrivileged(true)
	pinger.Count = 5

	err = pinger.Run() // Blocks until finished.

	if err != nil {
		return errors.WithStack(err)
	}

	stats := pinger.Statistics() // get send/receive/duplicate/rtt stats

	// AvgRtt in Nanoseconds / 1e6 -> yields average rtt in milliseconds
	// average rtt / 2.0 -> yields one way latency
	p.latency = (float64(stats.AvgRtt.Nanoseconds()) / 1e6) / 2.0

	log.Debugf("Latency %.1f", p.latency)

	log.Infof("Determined a latency of %.1f to host %s", p.latency, p.directAddr)

	return nil
}

func (o *Orchestrator) registerLocal(sat uint64, shell int64, name string) error {
	for _, host := range o.remoteHosts {
		conn, err := grpc.Dial(net.JoinHostPort(host.directAddr.String(), host.grpcPort), grpc.WithInsecure())

		if err != nil {
			return errors.WithStack(err)

		}

		_, err = peering.NewPeeringClient(conn).Route(context.Background(), &peering.RouteRequest{
			Machine: &peering.Machine{
				Shell: shell,
				Id:    sat,
				Name:  name,
			},
			Index: o.ownID,
		})

		if err != nil {
			return errors.WithStack(err)
		}
	}

	return nil
}

func (m *machine) routeRemote() error {
	// ip route del [MACHINE_NETWORK]
	// make sure there is no old route here: this can fail
	cmd := exec.Command("ip", "route", "del", m.network.String())

	_, _ = cmd.CombinedOutput()

	// ip route add [MACHINE_NETWORK] via [REMOTE_WG_ADDR] dev [WGINTERFACE]
	cmd = exec.Command("ip", "route", "add", m.network.String(), "via", m.remoteMachine.host.wgAddr.String(), "dev", WGINTERFACE)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (o *Orchestrator) RouteMachine(m commons.MachineID, bandwidth uint64, host uint64) error {
	// check if that shell even exists
	s, ok := o.shells[shellid(m.Shell)]

	if !ok {
		return errors.Errorf("unknown shell: %d", m.Shell)
	}

	// check if the machine exists already
	s.RLock()
	if _, ok := s.machines[id(m.ID)]; ok {
		s.RUnlock()
		return errors.Errorf("machine exists already: %d in in shell %d", m.ID, m.Shell)
	}
	s.RUnlock()

	ip, _, _, _, _, _, err := getIPAddressMACAndTapName(m.Shell, m.ID)

	if err != nil {
		return errors.WithStack(err)
	}

	ipIP, ipNet, err := net.ParseCIDR(ip)

	if err != nil {
		return errors.WithStack(err)
	}

	machine := &machine{
		isLocal:       false,
		remoteMachine: &remoteMachine{},
		id:            id(m.ID),
		address:       ipIP,
		network:       ipNet,
		bandwidth:     bandwidth,
	}

	s.Lock()
	s.machines[id(m.ID)] = machine
	s.Unlock()

	h, ok := o.remoteHosts[host]

	if !ok {
		return errors.Errorf("unknown host %d", host)
	}

	if m.Shell == -1 {
		o.gstLock.Lock()
		o.groundstations[m.Name] = machine
		o.gstLock.Unlock()
	}

	machine.remoteMachine.host = h

	h.allowedNets = append(h.allowedNets, machine.network)

	allowedCIDRs := h.wgAddr.String() + "/32"

	for _, n := range h.allowedNets {
		allowedCIDRs += ","
		allowedCIDRs += n.String()
	}

	// wg set [WGINTERFACE] peer [PEER_PUBLICKEY] allowed-ips [PEER_WG_ADDR]/32,[MACHINE_1_NET],[MACHINE_2_NET],...
	cmd := exec.Command("wg", "set", WGINTERFACE, "peer", h.publickey, "allowed-ips", allowedCIDRs)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return machine.routeRemote()
}
