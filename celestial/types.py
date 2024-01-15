from enum import Enum
import typing

import numpy as np

timestamp_s = int


class VMState(Enum):
    STOPPED = 0
    ACTIVE = 1


# class MachineID:
#     def __init__(
#         self,
#         group: int,
#         id: int,
#         name: typing.Optional[str] = None,
#     ):
#         self.group = group
#         self.id = id
#         self.name = name

#     def __repr__(self) -> str:
#         return f"MachineID(group={self.group}, id={self.id}, name={self.name})"

#     def __eq__(self, __value: object) -> bool:
#         if not isinstance(__value, MachineID):
#             return False

#         return (
#             self.group == __value.group
#             and self.id == __value.id
#             and self.name == __value.name
#         )

#     def __hash__(self) -> int:
#         return hash((self.group, self.id))

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
