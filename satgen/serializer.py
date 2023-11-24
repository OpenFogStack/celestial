import typing
import satgen.types


class Serializer(typing.Protocol):
    def init_machine(
        self, machine: satgen.types.MachineID, config: satgen.config.MachineConfig
    ) -> None:
        ...

    def diff_link(
        self,
        t: satgen.types.timestep,
        source: satgen.types.MachineID,
        target: satgen.types.MachineID,
        link: satgen.types.Link,
    ) -> None:
        ...

    def diff_machine(
        self,
        t: satgen.types.timestep,
        machine: satgen.types.MachineID,
        s: satgen.types.VMState,
    ) -> None:
        ...

    def persist(self) -> None:
        ...
