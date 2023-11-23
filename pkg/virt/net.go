package virt

import (
	"fmt"
	"net"
	"os/exec"

	"github.com/pkg/errors"

	orchestrator "github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

// getNet returns an IP Address (CIDR format), a custom MAC address, and a tap name for a given
// machine identifier. Group is limited to 8 bits (max. 256) and ID to 14 bits (max. 16,384) because of IPv4. In
// theory, we could split this up differently, so that shell has 6 bits and ID 16 bits, etc. This limit is enforced
// and is also used to ensure the tap device name is less than 14 digits long. Each tap has to have its own network,
// that network is 10.[shell].[id>>6 & 0xFF].[id<<2 & 0xFF]/30, leaves 3 addresses on that network: network + 1 is
// gateway IP, network + 2 is tap IP.
// Ground stations are in shell 0, satellite shells start at 1.
// TODO: test this
func getNet(id orchestrator.MachineID) (network, error) {

	if id.Id > 16384 {
		return network{}, errors.Errorf("id %d is larger than permitted 16,384", id)
	}

	return network{
		network: net.IPNet{IP: net.IP{10, id.Group & 0xFF, byte(((id.Id) >> 6) & 0xFF), byte(((id.Id)<<2)&0xFF + 0)}, Mask: net.CIDRMask(30, 32)},
		gateway: net.IPNet{IP: net.IP{10, id.Group & 0xFF, byte(((id.Id) >> 6) & 0xFF), byte(((id.Id)<<2)&0xFF + 1)}, Mask: net.CIDRMask(30, 32)},
		ip:      net.IPNet{IP: net.IP{10, id.Group & 0xFF, byte(((id.Id) >> 6) & 0xFF), byte(((id.Id)<<2)&0xFF + 2)}, Mask: net.CIDRMask(30, 32)},
		mac:     net.HardwareAddr{0xAA, 0xCE, (id.Group) & 0xFF, 0x00, byte(((id.Id + 2) >> 8) & 0xFF), byte(((id.Id + 2) >> 0) & 0xFF)},
		tap:     fmt.Sprintf("ct-%d-%d", id.Group, id.Id),
	}, nil
}

// TODO: test this
func getID(ip net.IP) (orchestrator.MachineID, error) {
	// do what getNet does, but in reverse
	if ip.To4() == nil {
		return orchestrator.MachineID{}, errors.Errorf("could not resolve IP address %s", ip.String())
	}

	if ip[0] != 10&0xFF {
		return orchestrator.MachineID{}, errors.Errorf("could not resolve IP address %s", ip.String())
	}

	return orchestrator.MachineID{
		Group: ip[1] & 0xFF,
		Id:    uint32((ip[2]<<6)&0xFF) + uint32(((ip[3]-2)>>2)&0xFF),
	}, nil
}

func (v *Virt) GetIPAddress(id orchestrator.MachineID) (net.IPNet, error) {
	n, err := getNet(id)

	if err != nil {
		return net.IPNet{}, errors.Wrap(err, "could not get network")
	}

	return n.ip, nil
}

func (v *Virt) ResolveIPAddress(ip net.IP) (orchestrator.MachineID, error) {
	// do what getNet does, but in reverse
	return getID(ip)
}

// removeNetworkDevice removes a network device. Errors are ignored.
func removeNetworkDevice(tapName string, hostInterface string) {
	// ip link del [TAP_NAME]

	cmd := exec.Command(IP_BIN, "link", "del", tapName)

	_ = cmd.Run()

	// iptables -D FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command(IPTABLES_BIN, "-D", "FORWARD", "-i", tapName, "-o", hostInterface, "-j", "ACCEPT")

	_ = cmd.Run()
}

// createNetworkDevice creates a new network device for a microVM.
func createNetworkDevice(gateway net.IPNet, tapName string, hostInterface string) error {

	// ip tuntap add [TAP_NAME] mode tap

	cmd := exec.Command(IP_BIN, "tuntap", "add", tapName, "mode", "tap")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// set up proxy ARP
	// sysctl -w net.ipv4.conf.[TAP_NAME].proxy_arp=1
	cmd = exec.Command(SYSCTL_BIN, "-w", fmt.Sprintf("net.ipv4.conf.%s.proxy_arp=1", tapName))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// disable ipv6
	// sysctl -w net.ipv6.conf.[TAP_NAME].disable_ipv6=1
	cmd = exec.Command(SYSCTL_BIN, "-w", fmt.Sprintf("net.ipv6.conf.%s.disable_ipv6=1", tapName))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip addr add [IP_ADDRESS] dev [TAP_NAME]

	cmd = exec.Command(IP_BIN, "addr", "add", gateway.String(), "dev", tapName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip link set [TAP_NAME] up

	cmd = exec.Command(IP_BIN, "link", "set", tapName, "up")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -A FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command(IPTABLES_BIN, "-A", "FORWARD", "-i", tapName, "-o", hostInterface, "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}
