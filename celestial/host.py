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
import typing

import celestial.types
import celestial.config
import proto.celestial.celestial_pb2
import proto.celestial.celestial_pb2_grpc


class Host:
    def __init__(self, num: int, addr: str):
        self.num = num
        self.addr = addr

        c = grpc.insecure_channel(self.addr)
        self.stub = proto.celestial.celestial_pb2_grpc.CelestialStub(c)

        self.public_key = ""

    def register(self) -> proto.celestial.celestial_pb2.RegisterResponse:
        request = proto.celestial.celestial_pb2.RegisterRequest(host=self.num)

        response = self.stub.Register(request)

        # others currently not used
        self.peer_public_key = response.peer_public_key

        self.peer_listen_addr = (
            self.addr.split(":")[0] + ":" + response.peer_listen_addr.split(":")[1]
        )

        print(f"host {self.num} registered")
        print(f"memory: {response.available_ram}")
        print(f"cpu: {response.available_cpus}")

        return response

    def init(
        self,
        hosts: typing.List["Host"],
        machines: typing.Dict[
            int,
            typing.List[
                typing.Tuple[
                    celestial.types.MachineID_dtype, celestial.config.MachineConfig
                ]
            ],
        ],
    ) -> None:
        init_request = proto.celestial.celestial_pb2.InitRequest()

        for h in hosts:
            k = proto.celestial.celestial_pb2.InitRequest.Host(
                id=h.num,
                peer_public_key=h.peer_public_key,
                peer_listen_addr=h.peer_listen_addr,
            )
            init_request.hosts.append(k)

            for m in machines[h.num]:
                mid = proto.celestial.celestial_pb2.MachineID(
                    group=celestial.types.MachineID_group(m[0]),
                    id=celestial.types.MachineID_id(m[0]),
                    name=celestial.types.MachineID_name(m[0]),
                )

                mc = proto.celestial.celestial_pb2.InitRequest.Machine.MachineConfig(
                    vcpu_count=m[1].vcpu_count,
                    ram=m[1].mem_size_mib,
                    disk_size=m[1].disk_size,
                    root_image=m[1].rootfs,
                    kernel=m[1].kernel,
                    boot_parameters=m[1].boot_parameters,
                )

                m = proto.celestial.celestial_pb2.InitRequest.Machine(
                    id=mid, config=mc, host=h.num
                )

                init_request.machines.append(m)

        self.stub.Init(init_request)

        return

    def stop(self) -> None:
        self.stub.Stop(proto.celestial.celestial_pb2.Empty())

    def update(
        self,
        machine_diff: typing.List[
            typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
        ],
        link_diff: typing.List[
            typing.Tuple[
                celestial.types.MachineID_dtype,
                celestial.types.MachineID_dtype,
                celestial.types.Link_dtype,
            ]
        ],
    ) -> None:
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

        self.stub.Update(update_request)

        return
