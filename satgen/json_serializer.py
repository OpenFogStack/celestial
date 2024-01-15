import satgen.config
import satgen.types


class JSONSerializer:
    def __init__(self, config: satgen.config.Config):
        self.filename = "{:08x}.json".format(hash(config))

        # clear file
        self.f = open(self.filename, "w")

    def init_machine(
        self,
        machine: satgen.types.MachineID_dtype,
        config: satgen.config.MachineConfig,
    ) -> None:
        self.f.write(
            f'{{"type":"init_machine","machine":{machine},"config":{config}}}\n'
        )

    def diff_link(
        self,
        t: satgen.types.timestamp_s,
        source: satgen.types.MachineID_dtype,
        target: satgen.types.MachineID_dtype,
        link: satgen.types.Link_dtype,
    ) -> None:
        self.f.write(
            f'{{"type":"diff_link","t":{t},"source":{source},"target":{target},"link":{link}}}\n'
        )

    def diff_machine(
        self,
        t: satgen.types.timestamp_s,
        machine: satgen.types.MachineID_dtype,
        s: satgen.types.VMState,
    ) -> None:
        self.f.write(
            f'{{"type":"diff_machine","t":{t},"machine":{machine},"state":{s}}}\n'
        )

    def persist(self) -> None:
        self.f.flush()
        self.f.close()
