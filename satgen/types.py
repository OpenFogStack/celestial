from enum import Enum
import typing

timestep = int


class VMState(Enum):
    STOPPED = 0
    ACTIVE = 1


class MachineID:
    def __init__(
        self,
        group: int,
        id: int,
        name: typing.Optional[str] = None,
    ):
        self.group = group
        self.id = id
        self.name = name


class Link:
    def __init__(
        self,
        latency: int,
        bandwidth: int,
        blocked: bool,
        next_hop: MachineID,
    ):
        self.latency = latency
        self.bandwidth = bandwidth
        self.blocked = blocked
        self.next = next_hop


MachineState = typing.Dict[
    MachineID,
    VMState,
]

MachineDiff = typing.Dict[
    MachineID,
    VMState,
]

LinkState = typing.Dict[
    MachineID,
    typing.Dict[
        MachineID,
        Link,
    ],
]

LinkDiff = typing.Dict[
    MachineID,
    typing.Dict[
        MachineID,
        Link,
    ],
]


class State:
    def __init__(
        self,
        machines_state: MachineState,
        links_state: LinkState,
    ):
        self.machines_state = machines_state
        self.links_state = links_state

    def diff_machines(self, other: "State") -> MachineDiff:
        # return diff of machines that have changed state from self to other
        d: MachineDiff = {}

        for machine, state in self.machines_state.items():
            if other.machines_state[machine] != state:
                d[machine] = other.machines_state[machine]

        return d

    def diff_links(self, other: "State") -> LinkDiff:
        # return diff of links that have changed state from self to other
        d: LinkDiff = {}

        for source, targets in self.links_state.items():
            for target, link in targets.items():
                if other.links_state[source][target] != link:
                    if source not in d:
                        d[source] = {}

                    d[source][target] = other.links_state[source][target]

        return d
