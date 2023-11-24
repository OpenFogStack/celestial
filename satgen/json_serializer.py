import typing
import satgen.types


class JSONSerializer:
    def __init__(self, filename: str):
        self.filename = filename

        # clear file
        self.f = open(self.filename, "w")

    def init_machine(
        self, machine: satgen.types.MachineID, config: satgen.config.MachineConfig
    ) -> None:
        self.f.write(
            f'{{"type":"init_machine","machine":{machine},"config":{config}}}\n'
        )

    def diff_link(
        self,
        t: satgen.types.timestep,
        source: satgen.types.MachineID,
        target: satgen.types.MachineID,
        link: satgen.types.Link,
    ) -> None:
        self.f.write(
            f'{{"type":"diff_link","t":{t},"source":{source},"target":{target},"link":{link}}}\n'
        )

    def diff_machine(
        self,
        t: satgen.types.timestep,
        machine: satgen.types.MachineID,
        s: satgen.types.VMState,
    ) -> None:
        self.f.write(
            f'{{"type":"diff_machine","t":{t},"machine":{machine},"state":{s}}}\n'
        )

    def persist(self) -> None:
        self.f.flush()
        self.f.close()
