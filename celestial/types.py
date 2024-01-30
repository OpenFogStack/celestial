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

"""Custom types used in Celestial"""

from enum import Enum
import typing

import numpy as np

timestamp_s = int


class VMState(Enum):
    """
    An enum for the state of a virtual machine, can be either stopped or active.
    """

    STOPPED = 0
    ACTIVE = 1


MachineID_dtype = typing.Tuple[np.uint8, np.uint16, str]


def MachineID(group: int, id: int, name: str = "") -> MachineID_dtype:
    """
    Generate a machine ID from a group, an ID and an optional name.

    :param group: The group of the machine.
    :param id: The ID of the machine.
    :param name: The name of the machine.

    :return: A machine ID.
    """
    return (np.uint8(group), np.uint16(id), name)


def MachineID_group(machine_id: MachineID_dtype) -> np.uint8:
    """
    Get the group of a machine ID.

    :param machine_id: The machine ID.
    :return: The group of the machine ID.
    """
    return machine_id[0]


def MachineID_id(machine_id: MachineID_dtype) -> np.uint16:
    """
    Get the ID of a machine ID.

    :param machine_id: The machine ID.
    :return: The ID of the machine ID.
    """
    return machine_id[1]


def MachineID_name(machine_id: MachineID_dtype) -> str:
    """
    Get the name of a machine ID.

    :param machine_id: The machine ID.
    :return: The name of the machine ID.
    """
    return machine_id[2]


Link_dtype = typing.Tuple[
    np.uint32, np.uint32, np.bool_, MachineID_dtype, MachineID_dtype
]


def Link(
    latency_us: int,
    bandwidth_kbits: int,
    blocked: bool,
    next_hop: MachineID_dtype,
    prev_hop: MachineID_dtype,
) -> Link_dtype:
    """
    Generate a link from a latency, a bandwidth, a blocked flag and a next hop.

    :param latency_us: The latency of the link in microseconds.
    :param bandwidth_kbits: The bandwidth of the link in kilobits per second.
    :param blocked: Whether the link is blocked.
    :param next_hop: The next hop of the link.
    """
    return (
        np.uint32(latency_us),
        np.uint32(bandwidth_kbits),
        np.bool_(blocked),
        next_hop,
        prev_hop,
    )


def Link_latency_us(link: Link_dtype) -> np.uint32:
    """
    Get the latency of a link.

    :param link: The link.
    :return: The latency of the link in microseconds.
    """
    return link[0]


def Link_bandwidth_kbits(link: Link_dtype) -> np.uint32:
    """
    Get the bandwidth of a link.

    :param link: The link.
    :return: The bandwidth of the link in kilobits per second.
    """
    return link[1]


def Link_blocked(link: Link_dtype) -> np.bool_:
    """
    Get the blocked flag of a link.

    :param link: The link.
    :return: Whether the link is blocked.
    """
    return link[2]


def Link_next_hop(link: Link_dtype) -> MachineID_dtype:
    """
    Get the next hop of a link.

    :param link: The link.
    :return: The next hop of the link.
    """
    return link[3]


def Link_prev_hop(link: Link_dtype) -> MachineID_dtype:
    """
    Get the previous hop of a link.

    :param link: The link.
    :return: The previous hop of the link.
    """
    return link[4]


MachineState = typing.Dict[
    MachineID_dtype,
    VMState,
]

MachineDiff = typing.Dict[
    MachineID_dtype,
    VMState,
]

LinkState = typing.Dict[
    MachineID_dtype,
    typing.Dict[
        MachineID_dtype,
        Link_dtype,
    ],
]

LinkDiff = typing.Dict[
    MachineID_dtype,
    typing.Dict[
        MachineID_dtype,
        Link_dtype,
    ],
]
