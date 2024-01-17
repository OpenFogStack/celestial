#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
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
import signal
import sys
import threading
import time
import typing

import proto.celestial.celestial_pb2
import proto.celestial.celestial_pb2_grpc
import celestial.types
import celestial.zip_serializer

DEBUG = True


class Host:
    def __init__(
        self, addr: str, stub: proto.celestial.celestial_pb2_grpc.CelestialStub
    ):
        self.addr = addr
        self.stub = stub
        self.public_key = ""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit(
            "Usage: python3 celestial.py [celestial.celestial] [host1] [host2] ... [host3]"
        )

    celestial_zip = sys.argv[1]

    serializer = celestial.zip_serializer.ZipDeserializer(celestial_zip)

    config = serializer.config()

    host_args = sys.argv[2:]
    hosts: typing.List[Host] = []

    for i in range(len(host_args)):
        c = grpc.insecure_channel(host_args[i])
        s = proto.celestial.celestial_pb2_grpc.CelestialStub(c)
        hosts.append(Host(host_args[i], s))
        if DEBUG:
            print(f"host {i}: {host_args[i]}")

    # init the constellation
    for i in range(len(hosts)):
        register_request = proto.celestial.celestial_pb2.RegisterRequest(host=i)

        register_response = hosts[i].stub.Register(register_request)

        hosts[i].public_key = register_response.public_key
        # others currently not used
        if DEBUG:
            print(f"host {i}: {register_response}")

    inits = serializer.init_machines()

    machines: typing.Dict[
        int, typing.List[proto.celestial.celestial_pb2.InitRequest.Machine]
    ] = {}
    count = 0

    for m_id, m_config in inits:
        mid = proto.celestial.celestial_pb2.MachineID(
            group=celestial.types.MachineID_group(m_id),
            id=celestial.types.MachineID_id(m_id),
            name=celestial.types.MachineID_name(m_id),
        )

        mc = proto.celestial.celestial_pb2.InitRequest.Machine.MachineConfig(
            vcpu_count=m_config.vcpu_count,
            ram=m_config.mem_size_mib,
            disk_size=m_config.disk_size,
            root_image=m_config.rootfs,
            kernel=m_config.kernel,
            boot_parameters=m_config.boot_parameters,
        )

        j = proto.celestial.celestial_pb2.InitRequest.Machine(
            id=mid, config=mc, host=count % len(hosts)
        )

        machines.setdefault(j.host, []).append(j)
        count += 1

    for i in range(len(hosts)):
        init_request = proto.celestial.celestial_pb2.InitRequest()

        for j in range(len(hosts)):
            k = proto.celestial.celestial_pb2.InitRequest.Host(
                id=j, addr=hosts[i].addr, publickey=hosts[i].public_key
            )
            init_request.hosts.append(k)

        for m in machines[i]:
            init_request.machines.append(m)

        hosts[i].stub.Init(init_request)

    def get_update(
        t: celestial.types.timestamp_s,
    ) -> proto.celestial.celestial_pb2.UpdateRequest:
        link_diff = serializer.diff_links(t)
        machine_diff = serializer.diff_machines(t)

        update_request = proto.celestial.celestial_pb2.UpdateRequest()

        for m_id, m_state in machine_diff:
            m_diff_id = proto.celestial.celestial_pb2.MachineID(
                group=celestial.types.MachineID_group(m_id),
                id=celestial.types.MachineID_id(m_id),
                name=celestial.types.MachineID_name(m_id),
            )

            m_diff_state = proto.celestial.celestial_pb2.VM_STATE_STOPPED
            if m_state == celestial.types.VMState.ACTIVE:
                m_diff_state = proto.celestial.celestial_pb2.VM_STATE_ACTIVE

            m_diff = proto.celestial.celestial_pb2.UpdateRequest.MachineDiff(
                id=m_diff_id, active=m_diff_state
            )

            # print(f"switching {m_id} to {m_state}")

            update_request.machine_diffs.append(m_diff)

        network_diffs: typing.Dict[
            celestial.types.MachineID_dtype,
            proto.celestial.celestial_pb2.UpdateRequest.NetworkDiff.Link,
        ] = {}

        for source, target, link in link_diff:
            l_diff_source = proto.celestial.celestial_pb2.MachineID(
                group=celestial.types.MachineID_group(source),
                id=celestial.types.MachineID_id(source),
                name=celestial.types.MachineID_name(source),
            )

            l_diff_target = proto.celestial.celestial_pb2.MachineID(
                group=celestial.types.MachineID_group(target),
                id=celestial.types.MachineID_id(target),
                name=celestial.types.MachineID_name(target),
            )

            l_diff_next = proto.celestial.celestial_pb2.MachineID(
                group=celestial.types.MachineID_group(
                    celestial.types.Link_next_hop(link)
                ),
                id=celestial.types.MachineID_id(celestial.types.Link_next_hop(link)),
                name=celestial.types.MachineID_name(
                    celestial.types.Link_next_hop(link)
                ),
            )

            source_l_diff = (
                proto.celestial.celestial_pb2.UpdateRequest.NetworkDiff.Link(
                    target=l_diff_target,
                    latency=celestial.types.Link_latency_us(link),
                    bandwidth=celestial.types.Link_bandwidth_kbits(link),
                    blocked=bool(celestial.types.Link_blocked(link)),
                    next=l_diff_next,
                )
            )

            # do the other direction as well...
            target_l_diff = (
                proto.celestial.celestial_pb2.UpdateRequest.NetworkDiff.Link(
                    target=l_diff_source,
                    latency=celestial.types.Link_latency_us(link),
                    bandwidth=celestial.types.Link_bandwidth_kbits(link),
                    blocked=bool(celestial.types.Link_blocked(link)),
                    next=l_diff_next,
                )
            )

            network_diffs.setdefault(source, []).append(source_l_diff)
            network_diffs.setdefault(target, []).append(target_l_diff)

            # print(
            # f"changing link {source} to {l_diff_target} to {celestial.types.Link_blocked(link)}"
            # )

            # if DEBUG:
            # print(f"link diff: {source} -> {target} {source_l_diff}")
            # if celestial.types.MachineID_group(source) == 0:
            # print(
            # f"link diff: {source} -> {target} {source_l_diff} {source_l_diff.blocked}"
            # )

        for source, links in network_diffs.items():
            n_diff_source = proto.celestial.celestial_pb2.MachineID(
                group=celestial.types.MachineID_group(source),
                id=celestial.types.MachineID_id(source),
                name=celestial.types.MachineID_name(source),
            )

            n_diff = proto.celestial.celestial_pb2.UpdateRequest.NetworkDiff(
                id=n_diff_source,
                links=links,
            )

            update_request.network_diffs.append(n_diff)

        return update_request

    # start the simulation
    timestep: celestial.types.timestamp_s = 0
    update_request = get_update(timestep)
    start_time = time.perf_counter()
    print("starting simulation")

    # install sigterm handler
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        while True:
            print(f"timestep: {timestep}")

            def update(host: Host) -> None:
                host.stub.Update(update_request)

            t: typing.List[threading.Thread] = []

            for i in range(len(hosts)):
                x = threading.Thread(target=update, args=(hosts[i],))
                x.start()
                print(f"sent update request to host {i}")
                t.append(x)

            for i in range(len(hosts)):
                t[i].join()

            timestep += config.resolution

            if timestep > config.duration:
                break

            print(f"getting update for timestep {timestep}")
            update_request = get_update(timestep)

            print(f"waiting for {timestep -(time.perf_counter() - start_time)} seconds")
            while time.perf_counter() - start_time < timestep:
                time.sleep(0.001)

    finally:
        print("got keyboard interrupt, stopping...")
        for i in range(len(hosts)):
            hosts[i].stub.Stop(proto.celestial.celestial_pb2.Empty())
        print("finished")
