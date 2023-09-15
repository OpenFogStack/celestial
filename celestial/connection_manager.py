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

import grpc
import typing
import threading as td
import typing
import time
import tqdm

from .machine_connector import MachineConnector
from .types import ShellConfig

from proto.celestial import celestial_pb2, celestial_pb2_grpc


class ConnectionManager:
    def __init__(
        self,
        hosts: typing.List[str],
        peeringhosts: typing.List[str],
        allowed_concurrent: int = 512,
    ):
        stubs: typing.List[celestial_pb2_grpc.CelestialStub] = []

        for host in hosts:
            channel = grpc.insecure_channel(host)
            stubs.append(celestial_pb2_grpc.CelestialStub(channel))

        self.hosts = hosts

        self.allowed_concurrent = allowed_concurrent

        irr = celestial_pb2.InitRemotesRequest()

        for i in range(len(peeringhosts)):
            r = celestial_pb2.RemoteHost()
            r.index = i
            r.addr = peeringhosts[i]

            irr.remotehosts.append(r)

        for i in range(len(self.hosts)):
            irr.index = i
            stubs[i].InitRemotes(irr)

        for i in range(len(self.hosts)):
            e = celestial_pb2.Empty()
            stubs[i].StartPeering(e)

    def init_mutex(self) -> None:
        self.stubs: typing.List[celestial_pb2_grpc.CelestialStub] = []

        for host in self.hosts:
            channel = grpc.insecure_channel(host)
            self.stubs.append(celestial_pb2_grpc.CelestialStub(channel))

        self.mutexes: typing.Dict[str, td.Semaphore] = {}

        for host in self.hosts:
            self.mutexes[host] = td.Semaphore(self.allowed_concurrent)

    def __register(
        self,
        conn: MachineConnector,
        bandwidth: int,
        active: bool,
        vcpu_count: int,
        mem_size_mib: int,
        ht_enabled: bool,
        disk_size_mib: int,
        kernel: str,
        rootfs: str,
        bootparams: str,
    ) -> None:
        self.mutexes[conn.host].acquire()
        try:
            conn.create_machine(
                vcpu_count=vcpu_count,
                mem_size_mib=mem_size_mib,
                ht_enabled=ht_enabled,
                disk_size_mib=disk_size_mib,
                kernel=kernel,
                rootfs=rootfs,
                bootparams=bootparams,
                active=active,
                bandwidth=bandwidth,
            )
        except Exception as e:
            print(
                "❌ caught exception while trying to create machine %d shell %d:"
                % (conn.id, conn.shell),
                e,
            )

        self.mutexes[conn.host].release()

    def register_machine(
        self,
        shell_no: int,
        id: int,
        bandwidth: int,
        active: bool,
        vcpu_count: int,
        mem_size_mib: int,
        ht_enabled: bool,
        disk_size_mib: int,
        kernel: str,
        rootfs: str,
        bootparams: str,
        host_affinity: typing.List[int],
        name: str = "",
    ) -> MachineConnector:
        # assign a random stub to this connection
        #
        # how do we get a host for a machine? serveral possibilities
        # easiest: random distribution:
        #   host = self.hosts[random.randint(0,len(self.hosts)-1)]
        # not very efficient and fair though
        #
        # better: even distribution
        #   host = self.hosts[id % len(self.hosts)]
        # issue: each ISL has to pass to a different machine

        host = self.hosts[host_affinity[id % len(host_affinity)]]
        stub = self.stubs[host_affinity[id % len(host_affinity)]]

        conn = MachineConnector(stub=stub, host=host, shell=shell_no, id=id, name=name)

        td.Thread(
            target=self.__register,
            kwargs={
                "conn": conn,
                "vcpu_count": vcpu_count,
                "mem_size_mib": mem_size_mib,
                "ht_enabled": ht_enabled,
                "disk_size_mib": disk_size_mib,
                "kernel": kernel,
                "rootfs": rootfs,
                "bootparams": bootparams,
                "active": active,
                "bandwidth": bandwidth,
            },
        ).start()

        return conn

    def collect_host_infos(self) -> typing.Tuple[int, int, int]:
        cpu_count = 0
        mem = 0
        machine_count = 0

        for host in self.hosts:
            channel = grpc.insecure_channel(host)

            stub = celestial_pb2_grpc.CelestialStub(channel)

            r = celestial_pb2.Empty()

            info = stub.GetHostInfo(r)

            machine_count += 1
            cpu_count += info.cpu
            mem += info.mem / 1000000

        return machine_count, cpu_count, mem

    def block_host_ready(self, tbar: tqdm.tqdm, total_machines: int) -> None:
        ready = [False] * len(self.hosts)
        total = [0] * len(self.hosts)

        time.sleep(2.5)

        while not all(ready):
            for i in range(len(self.hosts)):
                if ready[i]:
                    continue

                channel = grpc.insecure_channel(self.hosts[i])

                stub = celestial_pb2_grpc.CelestialStub(channel)

                r = celestial_pb2.Empty()

                ready_info = stub.HostReady(r)

                if ready_info.ready == True:
                    ready[i] = True

                old = sum(total)
                total[i] = ready_info.created
                tbar.update(sum(total) - old)

            time.sleep(5)

        tbar.close()

        if not sum(total) == total_machines:
            raise ValueError("reported created machines not equal total machines")

    def init(
        self,
        db: bool,
        db_host: typing.Optional[str],
        shell_count: int,
        shells: typing.List[ShellConfig],
    ) -> None:
        isr = celestial_pb2.InitRequest()

        isr.database = db

        if db and db_host is not None:
            isr.databaseHost = db_host

        isr.shellcount = shell_count

        for i in range(len(shells)):
            s = celestial_pb2.Shell()
            s.id = i
            s.planes = shells[i].planes
            isr.shells.append(s)

        for host in self.hosts:
            channel = grpc.insecure_channel(host)

            stub = celestial_pb2_grpc.CelestialStub(channel)

            res = stub.Init(isr)
