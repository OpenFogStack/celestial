import typing
import satgen.types


class Serializer(typing.Protocol):
    def init_machine(
        self, machine: satgen.types.MachineID_dtype, config: satgen.config.MachineConfig
    ) -> None:
        ...

    def diff_link(
        self,
        t: satgen.types.timestamp_s,
        source: satgen.types.MachineID_dtype,
        target: satgen.types.MachineID_dtype,
        link: satgen.types.Link_dtype,
    ) -> None:
        ...

    def diff_machine(
        self,
        t: satgen.types.timestamp_s,
        machine: satgen.types.MachineID_dtype,
        s: satgen.types.VMState,
    ) -> None:
        ...

    def persist(self) -> None:
        ...


class Deserializer(typing.Protocol):
    def config(self) -> satgen.config.Config:
        ...

    def init_machine(
        self,
    ) -> typing.List[
        typing.Tuple[satgen.types.MachineID_dtype, satgen.config.MachineConfig]
    ]:
        ...

    def diff_links(
        self, t: satgen.types.timestamp_s
    ) -> typing.List[
        typing.Tuple[
            satgen.types.MachineID_dtype,
            satgen.types.MachineID_dtype,
            satgen.types.Link_dtype,
        ]
    ]:
        ...

    def diff_machines(
        self, t: satgen.types.timestamp_s
    ) -> typing.List[typing.Tuple[satgen.types.MachineID_dtype, satgen.types.VMState]]:
        ...
