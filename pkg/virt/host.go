package virt

import (
	"io/fs"
	"os"
	"os/exec"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

// initHost resets the hosts iptables and sets up basics on the host.
// Partially based on https://github.com/firecracker-microvm/firecracker-demo/blob/main/one-time-setup.sh
func (v *Virt) initHost() error {

	// clear iptables
	// iptables -F
	cmd := exec.Command(IPTABLES_BIN, "-F")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"

	file, err := os.Create("/proc/sys/net/ipv4/ip_forward")

	if err != nil {
		return err
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

	// Configure packet forwarding
	// sysctl -wq net.ipv4.conf.all.forwarding=1

	cmd = exec.Command(SYSCTL_BIN, "-wq", "net.ipv4.conf.all.forwarding=1")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// Avoid "neighbour: arp_cache: neighbor table overflow!"
	// sysctl -wq net.ipv4.neigh.default.gc_thresh1=1024
	cmd = exec.Command(SYSCTL_BIN, "-wq", "net.ipv4.neigh.default.gc_thresh1=1024")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sysctl -wq net.ipv4.neigh.default.gc_thresh2=2048
	cmd = exec.Command(SYSCTL_BIN, "-wq", "net.ipv4.neigh.default.gc_thresh2=2048")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sysctl -wq net.ipv4.neigh.default.gc_thresh3=4096
	cmd = exec.Command(SYSCTL_BIN, "-wq", "net.ipv4.neigh.default.gc_thresh3=4096")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	//sudo iptables -t nat -A POSTROUTING -o [HOSTINTERFACE] -j MASQUERADE

	cmd = exec.Command(IPTABLES_BIN, "-t", "nat", "-A", "POSTROUTING", "-o", v.hostInterface, "-j", "MASQUERADE")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

	cmd = exec.Command(IPTABLES_BIN, "-A", "FORWARD", "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED", "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// prepare an output folder

	// prepare the file writers for output
	// if the directory exists, remove it
	if _, err = os.Stat(OUTPUTPATH); err == nil {
		err = os.RemoveAll(OUTPUTPATH)

		if err != nil {
			return err
		}
	}

	// then create it
	err = os.Mkdir(OUTPUTPATH, fs.FileMode(0755))
	if err != nil {
		return err
	}

	return nil
}
