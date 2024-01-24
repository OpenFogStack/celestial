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

"""A protocol for serializers and deserializers"""

import typing
import celestial.types


class Serializer(typing.Protocol):
    """
    A serializer takes constellation updates and serializes it into a format
    that can be used for emulation.
    """

    def init_machine(
        self,
        machine: celestial.types.MachineID_dtype,
        config: celestial.config.MachineConfig,
    ) -> None:
        """
        Serialize a machine initialization.

        :param machine: The machine ID of the machine.
        :param config: The configuration of the machine.
        """
        ...

    def diff_link(
        self,
        t: celestial.types.timestamp_s,
        source: celestial.types.MachineID_dtype,
        target: celestial.types.MachineID_dtype,
        link: celestial.types.Link_dtype,
    ) -> None:
        """
        Serialize a link update.

        :param t: The timestamp of the update.
        :param source: The source machine of the link.
        :param target: The target machine of the link.
        :param link: The link.
        """
        ...

    def diff_machine(
        self,
        t: celestial.types.timestamp_s,
        machine: celestial.types.MachineID_dtype,
        s: celestial.types.VMState,
    ) -> None:
        """
        Serialize a machine state update.

        :param t: The timestamp of the update.
        :param machine: The machine ID of the machine.
        :param s: The state of the machine.
        """
        ...

    def persist(self) -> None:
        """
        Persist the serialized state. Called at the end of the simulation.
        """
        ...


class Deserializer(typing.Protocol):
    """
    Deserializes a serialized state into a constellation update.
    """

    def config(self) -> celestial.config.Config:
        """
        Get the configuration of the simulation.

        :return: The configuration of the simulation.
        """
        ...

    def init_machine(
        self,
    ) -> typing.List[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.config.MachineConfig]
    ]:
        """
        Deserialize the initial machine states.

        :return: A list of machine ID and machine configuration tuples.
        """
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
        """
        Deserialize the link updates.

        :param t: The timestamp of the update.
        :return: A list of link updates.
        """
        ...

    def diff_machines(
        self, t: celestial.types.timestamp_s
    ) -> typing.List[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
    ]:
        """
        Deserialize the machine state updates.

        :param t: The timestamp of the update.
        :return: A list of machine state updates.
        """
        ...
