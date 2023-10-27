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

# https://stackoverflow.com/a/33054922/12641379

import time
import typing
from threading import Event, Thread


class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval: int, function: typing.Callable[[], None]):
        self.interval = interval
        self.function = function
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self) -> None:
        while not self.event.wait(self._time):
            self.function()

    @property
    def _time(self) -> float:
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self) -> None:
        self.event.set()
        self.thread.join()
