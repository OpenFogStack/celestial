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

import typing
import celestial.types


class Serializer(typing.Protocol):
    def init_machine(
        self,
        machine: celestial.types.MachineID_dtype,
        config: celestial.config.MachineConfig,
    ) -> None:
        ...

    def diff_link(
        self,
        t: celestial.types.timestamp_s,
        source: celestial.types.MachineID_dtype,
        target: celestial.types.MachineID_dtype,
        link: celestial.types.Link_dtype,
    ) -> None:
        ...

    def diff_machine(
        self,
        t: celestial.types.timestamp_s,
        machine: celestial.types.MachineID_dtype,
        s: celestial.types.VMState,
    ) -> None:
        ...

    def persist(self) -> None:
        ...


class Deserializer(typing.Protocol):
    def config(self) -> celestial.config.Config:
        ...

    def init_machine(
        self,
    ) -> typing.List[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.config.MachineConfig]
    ]:
        ...

    def diff_links(
        self, t: celestial.types.timestamp_s
    ) -> typing.List[
        typing.Tuple[
            celestial.types.MachineID_dtype,
            celestial.types.MachineID_dtype,
            celestial.types.Link_dtype,
        ]
    ]:
        ...

    def diff_machines(
        self, t: celestial.types.timestamp_s
    ) -> typing.List[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
    ]:
        ...
