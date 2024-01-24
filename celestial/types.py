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

from enum import Enum
import typing

import numpy as np

timestamp_s = int


class VMState(Enum):
    STOPPED = 0
    ACTIVE = 1


MachineID_dtype = typing.Tuple[np.uint8, np.uint16, str]


def MachineID(group: int, id: int, name: str = "") -> MachineID_dtype:
    return (np.uint8(group), np.uint16(id), name)


def MachineID_group(machine_id: MachineID_dtype) -> np.uint8:
    return machine_id[0]


def MachineID_id(machine_id: MachineID_dtype) -> np.uint16:
    return machine_id[1]


def MachineID_name(machine_id: MachineID_dtype) -> str:
    return machine_id[2]


Link_dtype = typing.Tuple[np.uint32, np.uint32, np.bool_, MachineID_dtype]


def Link(
    latency_us: int,
    bandwidth_kbits: int,
    blocked: bool,
    next_hop: MachineID_dtype,
) -> Link_dtype:
    return (
        np.uint32(latency_us),
        np.uint32(bandwidth_kbits),
        np.bool_(blocked),
        next_hop,
    )


def Link_latency_us(link: Link_dtype) -> np.uint32:
    return link[0]


def Link_bandwidth_kbits(link: Link_dtype) -> np.uint32:
    return link[1]


def Link_blocked(link: Link_dtype) -> np.bool_:
    return link[2]


def Link_next_hop(link: Link_dtype) -> MachineID_dtype:
    return link[3]


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
