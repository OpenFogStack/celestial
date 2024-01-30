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

"""Adapter for communication with the Celestial hosts over gRPC"""

import grpc
import logging
import typing

import celestial.types
import celestial.config
import proto.celestial.celestial_pb2
import proto.celestial.celestial_pb2_grpc

MAX_DIFF_UPDATE_SIZE = 10_000


def make_init_request(
    hosts: typing.List["Host"],
    machines: typing.Dict[
        int,
        typing.List[
            typing.Tuple[
                celestial.types.MachineID_dtype, celestial.config.MachineConfig
            ]
        ],
    ],
) -> proto.celestial.celestial_pb2.InitRequest:
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
                id=mid,
                config=mc,
                host=h.num,
                name=celestial.types.MachineID_name(m[0]),
            )

            init_request.machines.append(m)

    return init_request


def make_update_request_iters(
    machine_diff_iter: typing.Iterator[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
    ],
    link_diff_iter: typing.Iterator[
        typing.Tuple[
            celestial.types.MachineID_dtype,
            celestial.types.MachineID_dtype,
            celestial.types.Link_dtype,
        ]
    ],
) -> typing.Iterator[proto.celestial.celestial_pb2.StateUpdateRequest]:
    """
    A function that returns a combined iterator of StateUpdateRequests based on
    iterating over machine_diff_iter and link_diff_iter.
    """
    count = 0

    update_request = proto.celestial.celestial_pb2.StateUpdateRequest()

    # iterate over all the machine diffs
    for m_id, m_state in machine_diff_iter:
        m_diff_id = proto.celestial.celestial_pb2.MachineID(
            group=celestial.types.MachineID_group(m_id),
            id=celestial.types.MachineID_id(m_id),
        )

        m_diff_state = proto.celestial.celestial_pb2.VM_STATE_STOPPED
        if m_state == celestial.types.VMState.ACTIVE:
            m_diff_state = proto.celestial.celestial_pb2.VM_STATE_ACTIVE

        m_diff = proto.celestial.celestial_pb2.StateUpdateRequest.MachineDiff(
            id=m_diff_id, active=m_diff_state
        )

        # append the machine diff to the update request and increase the count
        update_request.machine_diffs.append(m_diff)
        count += 1

        # if we have reached max diff size, yield the update request and reset it
        if count >= MAX_DIFF_UPDATE_SIZE:
            yield update_request
            update_request = proto.celestial.celestial_pb2.StateUpdateRequest()

            count = 0

    # when loop ends, we move on to the link diffs
    network_diffs: typing.Dict[
        celestial.types.MachineID_dtype,
        proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff.Link,
    ] = {}

    # iterate over all the link diffs
    for source, target, link in link_diff_iter:
        # append the link diff and increase counter
        network_diffs.setdefault(source, []).append(
            proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff.Link(
                target=proto.celestial.celestial_pb2.MachineID(
                    group=celestial.types.MachineID_group(target),
                    id=celestial.types.MachineID_id(target),
                ),
                latency=celestial.types.Link_latency_us(link),
                bandwidth=celestial.types.Link_bandwidth_kbits(link),
                blocked=bool(celestial.types.Link_blocked(link)),
                next=proto.celestial.celestial_pb2.MachineID(
                    group=celestial.types.MachineID_group(
                        celestial.types.Link_next_hop(link)
                    ),
                    id=celestial.types.MachineID_id(
                        celestial.types.Link_next_hop(link)
                    ),
                ),
                prev=proto.celestial.celestial_pb2.MachineID(
                    group=celestial.types.MachineID_group(
                        celestial.types.Link_prev_hop(link)
                    ),
                    id=celestial.types.MachineID_id(
                        celestial.types.Link_prev_hop(link)
                    ),
                ),
            )
        )

        # print("adding link")

        count += 1

        # once again, yield the update request and reset it if we reached max diff size
        if count >= MAX_DIFF_UPDATE_SIZE:
            # yielding requires translation of our dict into the protobuf format
            for source, links in network_diffs.items():
                n_diff_source = proto.celestial.celestial_pb2.MachineID(
                    group=celestial.types.MachineID_group(source),
                    id=celestial.types.MachineID_id(source),
                )

                n_diff = proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff(
                    id=n_diff_source,
                    links=links,
                )

                # can't append to links directly as protobufs don't have maps
                update_request.network_diffs.append(n_diff)

            # yield the update request and reset it
            yield update_request
            update_request = proto.celestial.celestial_pb2.StateUpdateRequest()
            # also reset our diff
            network_diffs = {}
            count = 0

    # loop ended, yield the last update request
    # yielding requires translation of our dict into the protobuf format again
    for source, links in network_diffs.items():
        n_diff_source = proto.celestial.celestial_pb2.MachineID(
            group=celestial.types.MachineID_group(source),
            id=celestial.types.MachineID_id(source),
        )

        n_diff = proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff(
            id=n_diff_source,
            links=links,
        )

        update_request.network_diffs.append(n_diff)

    yield update_request

    # done


class Host:
    """
    Communication link for a Celestial host.
    """

    def __init__(self, num: int, addr: str):
        """
        Initialize host communication.

        :param num: The host number.
        :param addr: The address of the host.
        """
        self.num = num
        self.addr = addr

        c = grpc.insecure_channel(self.addr)
        self.stub = proto.celestial.celestial_pb2_grpc.CelestialStub(c)

        self.public_key = ""

    def register(self) -> proto.celestial.celestial_pb2.RegisterResponse:
        """
        Send a `register` request to the host.

        :return: The response from the host.
        """
        request = proto.celestial.celestial_pb2.RegisterRequest(host=self.num)

        response = self.stub.Register(request)

        # others currently not used
        self.peer_public_key = response.peer_public_key

        self.peer_listen_addr = (
            self.addr.split(":")[0] + ":" + response.peer_listen_addr.split(":")[1]
        )

        logging.debug(f"host {self.num} registered")
        logging.debug(f"memory: {response.available_ram}")
        logging.debug(f"cpu: {response.available_cpus}")

        return response

    def init(
        self,
        init_request: proto.celestial.celestial_pb2.InitRequest,
    ) -> None:
        """
        Send an `init` request to the host.

        :param hosts: A list of all hosts in the constellation.
        :param machines: A dictionary mapping host numbers to a list of machine ID and machine configuration tuples.
        """

        self.stub.Init(init_request)

        return

    def stop(self) -> None:
        """
        Send a `stop` request to the host.
        """
        self.stub.Stop(proto.celestial.celestial_pb2.Empty())

    def update(
        self,
        machine_diff_iter: typing.Iterator[
            typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
        ],
        link_diff_iter: typing.Iterator[
            typing.Tuple[
                celestial.types.MachineID_dtype,
                celestial.types.MachineID_dtype,
                celestial.types.Link_dtype,
            ]
        ],
    ) -> None:
        """
        Send a `update` request to the host.

        :param machine_diff: An iterator of machine ID and machine state tuples.
        :param link_diff: An iterator of link tuples.
        """

        update_iterator = make_update_request_iters(machine_diff_iter, link_diff_iter)

        # logging.debug(f"have {len(list(update_iterator))} updates")

        self.stub.Update(update_iterator)

        return
