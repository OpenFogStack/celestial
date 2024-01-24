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

package orchestrator

import "net"

type VirtualizationBackend interface {
	RegisterMachine(machine MachineID, name string, host Host, config MachineConfig) error
	BlockLink(source MachineID, target MachineID) error
	UnblockLink(source MachineID, target MachineID) error
	SetLatency(source MachineID, target MachineID, latency uint32) error
	SetBandwidth(source MachineID, target MachineID, bandwidth uint64) error
	StopMachine(machine MachineID) error
	StartMachine(machine MachineID) error
	GetIPAddress(id MachineID) (net.IPNet, error)
	ResolveIPAddress(ip net.IP) (MachineID, error)
	Stop() error
}
