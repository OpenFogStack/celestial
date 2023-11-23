package peer2

import (
	"net"
	"os"
	"os/exec"
	"strconv"

	"github.com/go-ping/ping"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"

	orchestrator "github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

type HostInfo struct {
	Addr      string
	PublicKey string
}

type peer struct {
	directAddr  net.IP
	wgAddr      net.IP
	allowedNets []*net.IPNet
	port        uint16
	publicKey   string
	// microseconds
	latency uint64
}

type PeeringService struct {
	wgAddr      net.IP
	id          orchestrator.Host
	mask        string
	wgInterface string
	keyPath     string
	port        uint16

	publicKey string

	peers map[orchestrator.Host]*peer
}

func New(mask string, keypath string, wginterface string, port uint16) (*PeeringService, error) {
	// set up wireguard
	if _, err := exec.LookPath("wg"); err != nil {
		return nil, errors.Errorf("could not find wireguard on this machine: %s", err.Error())
	}

	// remove old stuff first
	// ip link del [WGINTERFACE]
	cmd := exec.Command("ip", "link", "del", wginterface)
	// errors are ok
	_ = cmd.Run()

	log.Debugf("Removed old wg interface")
	// wg genkey
	k, err := wgtypes.GeneratePrivateKey()

	if err != nil {
		return nil, errors.WithStack(err)
	}

	privatekey := k.String()

	privateKeyFile, err := os.Create(keypath)

	if err != nil {
		return nil, errors.WithStack(err)
	}

	defer func(privateKeyFile *os.File) {
		err := privateKeyFile.Close()
		if err != nil {
			log.Error(err.Error())
		}
	}(privateKeyFile)

	if _, err := privateKeyFile.WriteString(privatekey); err != nil {
		return nil, errors.WithStack(err)
	}

	p := k.PublicKey()
	pubkey := p.String()

	log.Debugf("Private key: %s Public key %s", privatekey, pubkey)

	return &PeeringService{
		mask:        mask,
		wgInterface: wginterface,
		keyPath:     keypath,
		port:        port,
		publicKey:   pubkey,
	}, nil
}

func (p *PeeringService) Register(host orchestrator.Host) (publickey string, err error) {
	wgaddr, err := getWGAddr(host)

	if err != nil {
		return "", errors.WithStack(err)
	}

	p.wgAddr = wgaddr
	p.id = host

	// ip link add [WGINTERFACE] type wireguard
	cmd := exec.Command("ip", "link", "add", p.wgInterface, "type", "wireguard")

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip addr add [OWN_WG_ADDRESS] dev [WGINTERFACE]
	cmd = exec.Command("ip", "addr", "add", p.wgAddr.String()+p.mask, "dev", p.wgInterface)

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// wg set [WGINTERFACE] private-key [PRIVATE_KEY_FILE] listen-port [WG_PORT]
	cmd = exec.Command("wg", "set", p.wgInterface, "private-key", p.keyPath, "listen-port", strconv.Itoa(int(p.port)))

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip link set [WGINTERFACE] up
	cmd = exec.Command("ip", "link", "set", p.wgInterface, "up")

	if out, err := cmd.CombinedOutput(); err != nil {
		return "", errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return p.publicKey, nil
}

func (p *PeeringService) GetHostID() (uint8, error) {
	if p.wgAddr == nil {
		return 0, errors.Errorf("not registered yet")
	}

	return uint8(p.id), nil
}

func (p *PeeringService) Route(network net.IPNet, host orchestrator.Host) error {
	// essentially, we just need to add the machine IP/Net to the list of allowed ips for this wireguard interface
	h, ok := p.peers[host]

	if !ok {
		return errors.Errorf("unknown host %d", host)
	}

	h.allowedNets = append(h.allowedNets, &network)

	// update the list of allowed IPs

	allowedCIDRs := h.wgAddr.String() + "/32"

	for _, n := range h.allowedNets {
		allowedCIDRs += ","
		allowedCIDRs += n.String()
	}

	// wg set [WGINTERFACE] peer [PEER_PUBLICKEY] allowed-ips [PEER_WG_ADDR]/32,[MACHINE_1_NET],[MACHINE_2_NET],...
	cmd := exec.Command("wg", "set", p.wgInterface, "peer", h.publicKey, "allowed-ips", allowedCIDRs)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func getWGAddr(host orchestrator.Host) (net.IP, error) {
	if host > 253 {
		return nil, errors.Errorf("index %d is larger than allowed 253", host)
	}

	// put into subnet 192.168.50.0/24
	return net.IPv4(0xC0, 0xA8, 0x32, byte(0x02+host)), nil
}

func (p *PeeringService) InitPeering(remotes map[orchestrator.Host]HostInfo) error {
	for remote, info := range remotes {
		if remote == p.id {
			continue
		}

		remoteWgAddr, err := getWGAddr(remote)

		if err != nil {
			return errors.WithStack(err)
		}

		addr, port, err := net.SplitHostPort(info.Addr)

		if err != nil {
			return errors.WithStack(err)
		}

		portNum, err := strconv.ParseUint(port, 10, 16)

		r := &peer{
			directAddr:  net.ParseIP(addr),
			wgAddr:      remoteWgAddr,
			allowedNets: []*net.IPNet{},
			port:        uint16(portNum),
			publicKey:   info.PublicKey,
		}

		// wg set [WGINTERFACE] peer [PEER_PUBLICKEY] allowed-ips [PEER_WG_ADDR]/32 endpoint [PEER_DIRECT_ADDR]:[WGPORT]
		cmd := exec.Command("wg", "set", p.wgInterface, "peer", r.publicKey, "allowed-ips", r.wgAddr.String()+"/32", "endpoint", net.JoinHostPort(r.directAddr.String(), port))

		if out, err := cmd.CombinedOutput(); err != nil {
			return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
		}

		// test latency to this peer
		pinger, err := ping.NewPinger(r.directAddr.String())

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

		// AvgRtt in Nanoseconds / 1e9 -> yields average rtt in microseconds
		// average rtt / 2.0 -> yields one way latency
		r.latency = uint64((stats.AvgRtt.Nanoseconds() / 1e9) / 2.0)

		log.Debugf("Latency %dus", r.latency)

		log.Infof("Determined a latency of %dus to host %s", r.latency, r.directAddr)

		p.peers[remote] = r
	}

	return nil
}

func (p *PeeringService) Stop() error {
	return nil
}
