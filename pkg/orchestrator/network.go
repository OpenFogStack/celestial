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
	"fmt"
	"net"
	"os"
	"os/exec"

	"github.com/firecracker-microvm/firecracker-go-sdk"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/commons"
)

// GetIPAddress returns an IP address of a satellite machine.
func (o *Orchestrator) GetIPAddress(shell int64, id uint64) (string, error) {
	m, err := o.getMachine(commons.MachineID{
		Shell: shell,
		ID:    id})

	if err != nil {
		return "", errors.WithStack(err)
	}

	return m.address.String(), nil
}

// GetGSTIPAddress returns an IP address of a ground station machine.
func (o *Orchestrator) GetGSTIPAddress(name string) (string, error) {

	m, err := o.getGSTMachineByName(name)

	if err != nil {
		return "", errors.WithStack(err)
	}

	return m.address.String(), nil
}

// GetMachineByIP returns a machine identifier based on an IP address.
func (o *Orchestrator) GetMachineByIP(ip net.IP) (commons.MachineID, error) {

	ip = ip.To4()

	if ip[0] != 10&0xFF {
		return commons.MachineID{}, errors.Errorf("ip %s unknown", ip.String())
	}

	shell := int64(ip[1])

	if shell == 255 {
		shell = -1
	}

	id := uint64(ip[2]<<6) + uint64((ip[3]-2)>>2)

	m := commons.MachineID{
		Shell: shell,
		ID:    id,
	}

	machine, err := o.getMachine(m)

	if err != nil {
		return commons.MachineID{}, errors.WithStack(err)
	}

	return commons.MachineID{
		Shell: m.Shell,
		ID:    m.ID,
		Name:  machine.name,
	}, nil
}

// getIPAddressMACAndTapName returns an IP Address (CIDR format), a custom MAC address, and a tap name for a given
// machine identifier. Shell is limited to 8 bits (max. 256) and ID to 14 bits (max. 16,384) because of IPv4. I
// theory we could split this up differently, so that shell has 6 bits and ID 16 bits, etc. This limit is enforced
// and is also used to ensure the tap device name is less than 14 digits long. Each tap has to have its own network,
// that network is 10.[shell].[id>>6 & 0xFF].[id<<2 & 0xFF]/30, leaves 3 addresses on that network: network + 1 is
// gateway IP, network + 2 is tap IP.
// Since I'm bolting on support for ground stations now I have decided to give those the shell -1. As that would get
// us 0 (since we only check the last 8 bits), let's just invert that so we get a load of 1s. This should leave us
// with 255 for the second byte of the network/address. Because we're doing that, limit the shells to 255 as well.
func getIPAddressMACAndTapName(shell int64, id uint64) (ip string, gateway string, mac string, tapName string, chainName string, ipBlockSet string, err error) {

	if shell > 255 {
		err = errors.Errorf("shell %d is larger than permitted 256", shell)
		return
	}

	if shell < -1 {
		err = errors.Errorf("shell %d is lower than permitted -1", shell)
		return
	}

	if id > 16384 {
		err = errors.Errorf("id %d is larger than permitted 16,384", id)
	}

	// I tried the ^ operator first but I got a bit confused
	if shell == -1 {
		shell = 255
	}

	gateway = fmt.Sprintf("10.%d.%d.%d/30", shell&0xFF, ((id)>>6)&0xFF, ((id)<<2)&0xFF+1)
	ip = fmt.Sprintf("10.%d.%d.%d/30", shell&0xFF, ((id)>>6)&0xFF, ((id)<<2)&0xFF+2)

	mac = net.HardwareAddr{0xAA, 0xCE, byte((shell) & 0xFF), 0x00, byte(((id + 2) >> 8) & 0xFF), byte(((id + 2) >> 0) & 0xFF)}.String()

	// tapName can be max 14 digits long
	// implicitly assuming that shell
	// tapName is "ct-[shell]-[id]" to limit length
	tapName = fmt.Sprintf("ct-%d-%d", shell, id)

	if shell == 255 {
		tapName = fmt.Sprintf("ct-gst-%d", id)
	}

	// chainName is "CT-[shell]-[id]" to limit length
	chainName = fmt.Sprintf("CT-%d-%d", shell, id)

	if shell == 255 {
		chainName = fmt.Sprintf("CT-GST-%d", id)
	}

	// ipBlockSet is "CT-[shell]-[id]-bl
	ipBlockSet = fmt.Sprintf("CT-%d-%d-bl", shell, id)

	if shell == 255 {
		ipBlockSet = fmt.Sprintf("CT-GST-%d-bl", id)
	}

	return
}

func getFirecrackerNetworkInterfaces(ip string, gateway string, mac string, tapName string) ([]firecracker.NetworkInterface, error) {

	ipIP, ipNet, err := net.ParseCIDR(ip)

	if err != nil {
		return nil, errors.WithStack(err)
	}

	gatewayIP, _, err := net.ParseCIDR(gateway)

	if err != nil {
		return nil, errors.WithStack(err)
	}

	config := firecracker.NetworkInterface{
		StaticConfiguration: &firecracker.StaticNetworkConfiguration{
			MacAddress:  mac,
			HostDevName: tapName,
			IPConfiguration: &firecracker.IPConfiguration{
				IPAddr: net.IPNet{
					IP:   ipIP,
					Mask: ipNet.Mask,
				},
				Gateway:     gatewayIP,
				Nameservers: []string{NAMESERVER},
				IfName:      GUESTINTERFACE,
			},
		},
	}

	// log.Infof("Static Network Configuration: %#v, IP Configuration: %#v with IP %s", *config.StaticConfiguration, *config.StaticConfiguration.IPConfiguration, config.StaticConfiguration.IPConfiguration.IPAddr.String())

	return []firecracker.NetworkInterface{config}, nil
}

// initHost resets the hosts iptables and sets up basics on the host.
func initHost(hostInterface string) error {

	// clear iptables
	// iptables -w -F
	cmd := exec.Command(IPTABLES, "-w", "-F")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"

	file, err := os.Create("/proc/sys/net/ipv4/ip_forward")

	if err != nil {
		log.Fatal(err)
	}

	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			log.Error(err.Error())
		}
	}(file)

	if _, err := file.WriteString("1"); err != nil {
		return errors.WithStack(err)
	}

	//sudo iptables -w -t nat -A POSTROUTING -o [HOSTINTERFACE] -j MASQUERADE

	cmd = exec.Command(IPTABLES, "-w", "-t", "nat", "-A", "POSTROUTING", "-o", hostInterface, "-j", "MASQUERADE")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sudo iptables -w -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

	cmd = exec.Command(IPTABLES, "-w", "-A", "FORWARD", "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED", "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

// createNetworkDevice creates a new network device for a microVM.
func createNetworkDevice(gateway string, tapName string, chainName string, ipBlockSet string, hostInterface string) error {

	// remove old network tap if exists
	err := removeNetworkDevice(tapName, chainName, ipBlockSet, hostInterface, true)

	if err != nil {
		return errors.WithStack(err)
	}

	// ip tuntap add [TAP_NAME] mode tap

	cmd := exec.Command("ip", "tuntap", "add", tapName, "mode", "tap")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip addr add [IP_ADDRESS] dev [TAP_NAME]

	cmd = exec.Command("ip", "addr", "add", gateway, "dev", tapName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ip link set [TAP_NAME] up

	cmd = exec.Command("ip", "link", "set", tapName, "up")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -A FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command(IPTABLES, "-w", "-A", "FORWARD", "-i", tapName, "-o", hostInterface, "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -N [CHAIN_NAME]

	cmd = exec.Command(IPTABLES, "-w", "-N", chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -A FORWARD -i [TAP_NAME] -j [CHAIN_NAME]

	cmd = exec.Command(IPTABLES, "-w", "-A", "FORWARD", "-i", tapName, "-j", chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ipset create [IP_BLOCK_SET] hash:net

	cmd = exec.Command(IPSET, "create", ipBlockSet, "hash:net")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -A [CHAIN_NAME] -m set --match-set [IP_BLOCK_SET] src -j REJECT --reject-with icmp-net-unreachable

	cmd = exec.Command(IPTABLES, "-w", "-A", chainName, "-m", "set", "--match-set", ipBlockSet, "src", "-j", "REJECT", "--reject-with", "icmp-net-unreachable")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

// removeNetworkDevice removes a network device.
func removeNetworkDevice(tapName string, chainName string, ipBlockSet string, hostInterface string, allowFail bool) error {
	// ip link del [TAP_NAME]

	cmd := exec.Command("ip", "link", "del", tapName)

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -D FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command(IPTABLES, "-w", "-D", "FORWARD", "-i", tapName, "-o", hostInterface, "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -D FORWARD -i [TAP_NAME] -j [CHAIN_NAME]

	cmd = exec.Command(IPTABLES, "-w", "-D", "FORWARD", "-i", tapName, "-j", chainName)

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -F [CHAIN_NAME]

	cmd = exec.Command(IPTABLES, "-w", "-F", chainName)

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -X [CHAIN_NAME]

	cmd = exec.Command(IPTABLES, "-w", "-X", chainName)
	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ipset destroy [IP_BLOCK_SET]

	cmd = exec.Command(IPSET, "destroy", ipBlockSet)
	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}
