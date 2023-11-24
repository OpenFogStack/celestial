import satgen.constellation
import satgen.types
import satgen.serializer

# TODO: find a reasonable default update threshold
# something like 10%? or 0.5ms?


class StateManager:
    def __init__(
        self,
        constellation: satgen.constellation.Constellation,
        writer: satgen.serializer.Serializer,
    ):
        self.constellation = constellation
        self.writer = writer

        machines = self.constellation.get_machines()

        self.state = satgen.types.State(
            machines_state={m: satgen.types.VMState.STOPPED for m in machines.keys()},
            links_state={
                m1: {
                    m2: satgen.types.Link(
                        latency=0, bandwidth=0, blocked=False, next_hop=m1
                    )
                    for m2 in machines.keys()
                    if m1 != m2
                }
                for m1 in machines.keys()
            },
        )

        for machine, config in machines.items():
            self.writer.init_machine(machine, config)

    def step(self, t: satgen.types.timestep) -> None:
        n = self.constellation.step(t)

        for machine, state in self.state.diff_machines(n).items():
            self.writer.diff_machine(t, machine, state)

        for source, source_links in self.state.diff_links(n).items():
            for target, link in source_links.items():
                self.writer.diff_link(t, source, target, link)

        self.state = n
