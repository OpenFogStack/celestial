#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import threading as td
import typing
import grpc

from proto.celestial import celestial_pb2, celestial_pb2_grpc

class MachineConnector():
    def __init__(
        self,
        stub: celestial_pb2_grpc.CelestialStub,
        host: str,
        shell: int,
        id: int,
        name: str=""
    ):

        self.stub = stub
        self.host = host

        self.shell = shell
        self.id = id
        self.name = name

    def create_machine(self, vcpu_count: int, mem_size_mib: int, ht_enabled: bool, disk_size_mib: int, kernel: str, rootfs: str, bootparams: str, active: bool, bandwidth: int) -> None:

        cmr = celestial_pb2.CreateMachineRequest()
        cmr.machine.shell = self.shell
        cmr.machine.id = self.id
        cmr.machine.name = self.name

        cmr.firecrackerconfig.vcpu = vcpu_count
        cmr.firecrackerconfig.mem = mem_size_mib
        cmr.firecrackerconfig.ht = ht_enabled
        cmr.firecrackerconfig.disk = disk_size_mib
        cmr.firecrackerconfig.kernel = kernel
        cmr.firecrackerconfig.rootfs = rootfs
        cmr.firecrackerconfig.bootparams = bootparams

        cmr.networkconfig.bandwidth = bandwidth

        cmr.status = active

        self.stub.CreateMachine(cmr)

    def modify_machine(self, active: bool) -> None:

        r = celestial_pb2.ModifyMachineRequest()

        r.machine.shell = self.shell
        r.machine.id = self.id

        r.status = active

        td.Thread(target=self.stub.ModifyMachine, args=(r,)).start()

    def modify_links(self, remove_set: typing.List[typing.Dict[str,int]], modify_set: typing.List[typing.Dict[str,typing.Union[int, float]]]) -> None:
        r = celestial_pb2.ModifyLinksRequest()

        r.a.shell = self.shell
        r.a.id = self.id

        for remove_link in remove_set:
            rl = celestial_pb2.RemoveLinkRequest()

            rl.b.shell = remove_link["shell"]
            rl.b.id = remove_link["sat"]

            r.remove.append(rl)

        for modify_link in modify_set:
            ml = celestial_pb2.ModifyLinkRequest()

            ml.b.shell = int(modify_link["shell"])
            ml.b.id = int(modify_link["sat"])

            ml.latency = float(modify_link["latency"])
            ml.bandwidth = int(modify_link["bandwidth"])

            r.modify.append(ml)

        if len(remove_set) + len(modify_set) > 0:
            self.stub.ModifyLinks(r)