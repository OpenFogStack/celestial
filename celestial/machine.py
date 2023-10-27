#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
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
import threading as td

from .machine_connector import MachineConnector

DEBUG = False

# update threshold for updating latency in ms
LATENCY_UPDATE_THRESHOLD = 0.5

# update threshold for updating bandwidth in Kbit
BANDWIDTH_UPDATE_THRESHOLD = 1


class Machine:
    def __init__(
        self,
        shell_no: int,
        plane_no: int,
        id: int,
        active: bool,
        machine_connector: MachineConnector,
    ):
        self.shell_no = shell_no
        self.plane_no = plane_no
        self.id = id

        self.active = active
        self.mutex = td.Semaphore(1)

        self.connector = machine_connector

        self.links: typing.Dict[
            Machine, typing.Dict[str, typing.Union[int, float]]
        ] = {}
        self.new_links: typing.Dict[
            Machine, typing.Dict[str, typing.Union[int, float]]
        ] = {}
        self.new_unlinks: typing.Set[Machine] = set()
        self.link_mutex = td.Semaphore(1)

    def reset_links(self) -> None:
        self.link_mutex.acquire()

        self.new_links = {}
        self.new_unlinks = set()

        self.link_mutex.release()

    def set_links(self) -> None:
        self.link_mutex.acquire()

        remove_set: typing.List[typing.Dict[str, int]] = []
        modify_set: typing.List[typing.Dict[str, typing.Union[int, float]]] = []

        for target in self.new_unlinks:
            remove_set.append(
                {
                    "shell": target.shell_no,
                    "sat": target.id,
                }
            )

            if DEBUG:
                print(
                    "removing delay from %s %s to %s %s"
                    % (self.shell_no, self.id, target.shell_no, target.id)
                )

        for target in self.links:
            if target not in self.new_links:
                # remove link
                remove_set.append(
                    {
                        "shell": target.shell_no,
                        "sat": target.id,
                    }
                )

                if DEBUG:
                    print(
                        "removing delay from %s %s to %s %s"
                        % (self.shell_no, self.id, target.shell_no, target.id)
                    )

        for target in self.new_links:
            if target in self.links:
                # modify link
                latency_diff = abs(
                    self.new_links[target]["latency"] - self.links[target]["latency"]
                )
                bandwidth_diff = abs(
                    self.new_links[target]["bandwidth"]
                    - self.links[target]["bandwidth"]
                )

                if (
                    not latency_diff > LATENCY_UPDATE_THRESHOLD
                    and not bandwidth_diff > BANDWIDTH_UPDATE_THRESHOLD
                ):
                    continue

            # add link
            modify_set.append(
                {
                    "shell": target.shell_no,
                    "sat": target.id,
                    "latency": self.new_links[target]["latency"],
                    "bandwidth": self.new_links[target]["bandwidth"],
                }
            )
            if DEBUG:
                print(
                    "modifying delay from %s %s to %s %s to: %d %d"
                    % (
                        self.shell_no,
                        self.id,
                        target.shell_no,
                        target.id,
                        self.new_links[target]["latency"],
                        self.new_links[target]["bandwidth"],
                    )
                )

        try:
            self.connector.modify_links(remove_set=remove_set, modify_set=modify_set)

        except Exception as e:
            print(
                "caught exception while trying to update links for machine %d shell %d:"
                % (self.id, self.shell_no),
                e,
            )

        finally:
            self.links = {}
            for target in self.new_links:
                self.links[target] = self.new_links[target]

        self.link_mutex.release()

    def link(self, target: "Machine", latency: float, bandwidth: int) -> None:
        self.link_mutex.acquire()

        if target in self.new_links:
            if latency < self.new_links[target]["latency"]:
                self.new_links[target] = {"latency": latency, "bandwidth": bandwidth}

        else:
            self.new_links[target] = {"latency": latency, "bandwidth": bandwidth}

        self.link_mutex.release()

    def unlink(self, targets: typing.Set["Machine"]) -> None:
        self.link_mutex.acquire()

        self.new_unlinks = self.new_unlinks.union(targets)

        self.link_mutex.release()

    def set_active(self, block: bool = False) -> None:
        t = td.Thread(target=self.__set_active)
        t.start()

        if block:
            t.join()

    def __set_active(self) -> None:
        self.mutex.acquire()

        if not self.active:
            try:
                self.active = True
                self.connector.modify_machine(self.active)
            except Exception as e:
                self.active = False
                print(
                    "caught exception while trying to set machine active %d shell %d:"
                    % (self.id, self.shell_no),
                    e,
                )

        self.mutex.release()

    def set_inactive(self, block: bool = False) -> None:
        t = td.Thread(target=self.__set_inactive)

        t.start()

        if block:
            t.join()

    def __set_inactive(self) -> None:
        self.mutex.acquire()

        if self.active:
            try:
                self.active = False
                self.connector.modify_machine(self.active)
            except Exception as e:
                self.active = True
                print(
                    "caught exception while trying to set machine inactive %d shell %d:"
                    % (self.id, self.shell_no),
                    e,
                )

        self.mutex.release()
