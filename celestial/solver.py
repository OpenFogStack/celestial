#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Ben S. Kempton, Tobias Pfandzelter, The OpenFogStack Team.
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
import numpy as np

# this is basically just an interface for our different solvers


class Solver(typing.Protocol):
    def init_sat_array(self, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        ...

    def set_time(self, time: int, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        ...
