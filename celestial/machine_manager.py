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
import numpy as np
import time
from tqdm.auto import tqdm
# import tqdm
from multiprocessing.connection import Connection as MultiprocessingConnection

from .machine import Machine
from .connection_manager import ConnectionManager
from .types import GroundstationConfig, ShellConfig, Path

class MachineManager():
    def __init__(
        self,
        shells: typing.List[ShellConfig],
        groundstations: typing.List[GroundstationConfig],
        constellation_conn: MultiprocessingConnection,
        connection_manager: ConnectionManager
        ):

        # save shell information
        self.shells = shells

        self.groundstations = groundstations

        self.connection_manager = connection_manager
        self.connection_manager.init_mutex()

        # pipe to talk to constellation
        self.constellation_conn = constellation_conn

        # wait for init message about constellation
        init = self.constellation_conn.recv()
        if type(init) != list or init[0] != "init":
            raise ValueError("Machine Manager: did not receive init message first!")

        self.init_machines(sat_positions=init[1])
        self.update_machines(sat_positions=init[1], paths=init[2], gst_sat_paths=init[3], gst_paths=init[4])
        self.constellation_conn.send(True)

        # start control handler that reacts to shell changes
        self.control_thread = td.Thread(target=self.control_thread_handler)
        self.control_thread.start()

    def init_machines(self, sat_positions: np.ndarray) -> None:
        if len(sat_positions) != len(self.shells):
            raise ValueError("Machine Manager: did not receive correct amount of shells for initialization")

        self.machines: typing.List[typing.List[Machine]] = []

        for s in range(len(self.shells)):
            machine_list: typing.List[Machine] = []

            for i in range(self.shells[s].planes):
                if self.shells[s].computeparams.vcpu_count > 0:
                    for j in range(self.shells[s].sats):

                        id = self.shells[s].sats * i + j

                        mc = self.connection_manager.register_machine(
                                    shell_no=s,
                                    id=id,
                                    bandwidth=self.shells[s].networkparams.bandwidth,
                                    active=sat_positions[s][id]["in_bbox"],
                                    vcpu_count=self.shells[s].computeparams.vcpu_count,
                                    mem_size_mib=self.shells[s].computeparams.mem_size_mib,
                                    ht_enabled=self.shells[s].computeparams.ht_enabled,
                                    disk_size_mib=self.shells[s].computeparams.disk_size_mib,
                                    kernel=self.shells[s].computeparams.kernel,
                                    rootfs=self.shells[s].computeparams.rootfs,
                                    bootparams=self.shells[s].computeparams.bootparams,
                                    host_affinity=self.shells[s].computeparams.hostaffinity,
                                )

                        machine_list.append(Machine(
                            shell_no=s,
                            plane_no=i,
                            id=id,
                            active=sat_positions[s][id]["in_bbox"],
                            machine_connector=mc
                        ))

            self.machines.append(machine_list)

        self.gst_machines: typing.List[Machine] = []

        for i in range(len(self.groundstations)):
            mc = self.connection_manager.register_machine(
                # ground stations get shell number -1 for now?
                shell_no=-1,
                id=i,
                name=self.groundstations[i].name,
                bandwidth=self.groundstations[i].networkparams.bandwidth,
                active=True,
                vcpu_count=self.groundstations[i].computeparams.vcpu_count,
                mem_size_mib=self.groundstations[i].computeparams.mem_size_mib,
                ht_enabled=self.groundstations[i].computeparams.ht_enabled,
                disk_size_mib=self.groundstations[i].computeparams.disk_size_mib,
                kernel=self.groundstations[i].computeparams.kernel,
                rootfs=self.groundstations[i].computeparams.rootfs,
                bootparams=self.groundstations[i].computeparams.bootparams,
                host_affinity=self.groundstations[i].computeparams.hostaffinity,
            )

            self.gst_machines.append(Machine(
                shell_no=-1,
                plane_no=-1,
                id=i,
                active=True,
                machine_connector=mc
            ))

        total_machines = len(self.groundstations)

        for s in range(len(self.shells)):
            total_machines += len(self.machines[s])

        self.connection_manager.block_host_ready(tqdm(total=total_machines, desc="Machine Setup", unit="machines"), total_machines)

    def __update_machines_in_shell(self, shell_no: int, sat_positions: typing.List[typing.Dict[str, typing.Union[float, bool]]]) -> None:
        for sat in self.machines[shell_no]:
            if sat_positions[sat.id]["in_bbox"]:
                if not sat.active:
                    sat.set_active()

            else:
                if sat.active:
                    sat.set_inactive()

        for sat in self.machines[shell_no]:
            sat.reset_links()

    def update_machines(self, sat_positions: typing.List[typing.List[typing.Dict[str, typing.Union[float, bool]]]], paths: typing.List[typing.List[Path]], gst_sat_paths: typing.List[typing.List[Path]], gst_paths: typing.List[typing.List[Path]]) -> None:

        # start_time = time.time()

        threads = []

        for shell_no in range(len(self.machines)):
            threads.append(td.Thread(target=self.__update_machines_in_shell, args=(shell_no, sat_positions[shell_no])))
            threads[shell_no].start()

        # threads_started_time = time.time()
        # print("threads started", threads_started_time - start_time)

        all_active_machines: typing.Set[Machine] = set()

        for shell_no in range(len(self.machines)):
            for sat in self.machines[shell_no]:
                if sat_positions[shell_no][sat.id]["in_bbox"]:
                    all_active_machines.add(sat)

        # active_sat_set_time = time.time()
        # print("active_sat_set_time", active_sat_set_time - threads_started_time)

        for gst_m in self.gst_machines:
            gst_m.reset_links()

        # gst_reset_links_time = time.time()
        # print("gst_reset_links_time", gst_reset_links_time - active_sat_set_time)

        for shell_no in range(len(self.machines)):
            threads[shell_no].join()

        # threads_joined_time = time.time()
        # print("threads_joined_time", threads_joined_time - gst_reset_links_time)

        unreachable: typing.Dict[Machine, typing.Set[Machine]] = {}

        all_active_machines = all_active_machines.union(self.gst_machines)

        for m in all_active_machines:
            unreachable[m] = all_active_machines.difference(set([m]))

        # prepare_unreachable_time = time.time()
        # print("prepare_unreachable_time", prepare_unreachable_time - threads_joined_time)

        for shell_no in range(len(self.machines)):
            if len(self.machines[shell_no]) > 0:
                for path in paths[shell_no]:
                    e1 = self.machines[shell_no][path.node_1]
                    e2 = self.machines[shell_no][path.node_2]

                    if e1.active and e2.active:

                        if e2 in unreachable[e1]:
                            unreachable[e1].remove(e2)
                        if e1 in unreachable[e2]:
                            unreachable[e2].remove(e1)

                        delay = path.delay
                        bandwidth = path.bandwidth

                        e1.link(e2, latency=delay, bandwidth=bandwidth)
                        e2.link(e1, latency=delay, bandwidth=bandwidth)

                for path in gst_sat_paths[shell_no]:

                    e1 = self.gst_machines[path.node_1]
                    e2 = self.machines[shell_no][path.node_2]

                    if e2.active:

                        if e2 in unreachable[e1]:
                            unreachable[e1].remove(e2)
                        if e1 in unreachable[e2]:
                            unreachable[e2].remove(e1)

                        delay = path.delay
                        bandwidth = path.bandwidth

                        e1.link(e2, latency=delay, bandwidth=bandwidth)
                        e2.link(e1, latency=delay, bandwidth=bandwidth)

            for path in gst_paths[shell_no]:

                e1 = self.gst_machines[path.node_1]
                e2 = self.gst_machines[path.node_2]

                if e2 in unreachable[e1]:
                    unreachable[e1].remove(e2)
                if e1 in unreachable[e2]:
                    unreachable[e2].remove(e1)

                delay = path.delay
                bandwidth = path.bandwidth

                e1.link(e2, latency=delay, bandwidth=bandwidth)
                e2.link(e1, latency=delay, bandwidth=bandwidth)

        # add_all_links_time = time.time()
        # print("add_all_links_time", add_all_links_time - prepare_unreachable_time)

        for m in unreachable:
            m.unlink(unreachable[m])

        # set_all_unlinks_time = time.time()
        # print("set_all_unlinks_time", set_all_unlinks_time - add_all_links_time)

        link_threads = set()

        for shell_no in range(len(self.machines)):
            for sat in self.machines[shell_no]:
                t = td.Thread(target=sat.set_links)
                t.start()
                link_threads.add(t)

        # start_link_threads_time = time.time()
        # print("start_link_threads_time", start_link_threads_time - set_all_unlinks_time)

        for gst_m in self.gst_machines:
            t = td.Thread(target=gst_m.set_links)
            t.start()
            link_threads.add(t)

        # threads_started_time2 = time.time()
        # print("threads_started_time2", threads_started_time2 - start_link_threads_time)

        for t in tqdm(link_threads):
            t.join()

        # threads_joined_time = time.time()
        # print("threads_joined_time", threads_joined_time - threads_started_time2)

        # print("total", threads_joined_time - start_time)

    def control_thread_handler(self) -> None:
        """
        Start a thread to deal with inter-process communications

        """
        while True:
            received_data = self.constellation_conn.recv()
            if type(received_data) == list:

                self.update_machines(sat_positions=received_data[0], paths=received_data[1], gst_sat_paths=received_data[2], gst_paths=received_data[3])
                self.constellation_conn.send(True)