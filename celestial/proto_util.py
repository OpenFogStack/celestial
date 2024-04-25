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

"""Utility functions for the Celestial gRPC protocol"""

import logging
import typing

import celestial.config
import celestial.host
import celestial.types
import proto.celestial.celestial_pb2
import proto.celestial.celestial_pb2_grpc


MAX_DIFF_UPDATE_SIZE = 100_000


def _machineID_group(m: celestial.types.MachineID_dtype) -> int:
    return typing.cast(int, celestial.types.MachineID_group(m))


def _machineID_id(m: celestial.types.MachineID_dtype) -> int:
    return typing.cast(int, celestial.types.MachineID_id(m))


def make_init_request(
    hosts: typing.List[celestial.host.Host],
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
                group=_machineID_group(m[0]),
                id=_machineID_id(m[0]),
            )

            mc = proto.celestial.celestial_pb2.InitRequest.Machine.MachineConfig(
                vcpu_count=m[1].vcpu_count,
                ram=m[1].mem_size_mib,
                disk_size=m[1].disk_size,
                root_image=m[1].rootfs,
                kernel=m[1].kernel,
                boot_parameters=m[1].boot_parameters,
            )

            r = proto.celestial.celestial_pb2.InitRequest.Machine(
                id=mid,
                config=mc,
                host=h.num,
                name=celestial.types.MachineID_name(m[0]),
            )

            init_request.machines.append(r)

    return init_request


T = typing.TypeVar("T")


def _islice(iterable: typing.Iterator[T], n: int) -> typing.Iterator[T]:
    count = 0

    for i in iterable:
        if count >= n:
            break

        yield i

        count += 1

    if count == 0:
        raise StopIteration


def make_update_request_iter(
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

    yield proto.celestial.celestial_pb2.StateUpdateRequest(
        machine_diffs=[
            proto.celestial.celestial_pb2.StateUpdateRequest.MachineDiff(
                id=proto.celestial.celestial_pb2.MachineID(
                    group=_machineID_group(m_id),
                    id=_machineID_id(m_id),
                ),
                active=proto.celestial.celestial_pb2.VM_STATE_STOPPED
                if m_state == celestial.types.VMState.STOPPED
                else proto.celestial.celestial_pb2.VM_STATE_ACTIVE,
            )
            for m_id, m_state in machine_diff_iter
        ],
    )

    try:
        while True:
            t = proto.celestial.celestial_pb2.StateUpdateRequest(
                network_diffs=[
                    proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff(
                        source=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(source),
                            id=_machineID_id(source),
                        ),
                        target=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(target),
                            id=_machineID_id(target),
                        ),
                        latency_us=typing.cast(
                            int, celestial.types.Link_latency_us(link)
                        ),
                        bandwidth_kbps=typing.cast(
                            int, celestial.types.Link_bandwidth_kbits(link)
                        ),
                        blocked=False,
                        next=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(celestial.types.Link_next_hop(link)),
                            id=_machineID_id(celestial.types.Link_next_hop(link)),
                        ),
                        prev=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(celestial.types.Link_prev_hop(link)),
                            id=_machineID_id(celestial.types.Link_prev_hop(link)),
                        ),
                    )
                    if not celestial.types.Link_blocked(link)
                    else proto.celestial.celestial_pb2.StateUpdateRequest.NetworkDiff(
                        source=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(source),
                            id=_machineID_id(source),
                        ),
                        target=proto.celestial.celestial_pb2.MachineID(
                            group=_machineID_group(target),
                            id=_machineID_id(target),
                        ),
                        blocked=True,
                    )
                    for source, target, link in _islice(
                        link_diff_iter, MAX_DIFF_UPDATE_SIZE
                    )
                ]
            )
            yield t
    except RuntimeError:
        # we reached the end of the link diff iterator
        # we just yield an empty update request
        # yield proto.celestial.celestial_pb2.StateUpdateRequest()

        # and we are done
        logging.debug("generating update requests done")
        return
