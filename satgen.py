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

import sys

import toml

import satgen.config
import satgen.json_serializer
import satgen.state_manager

if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 celestial.py [config.toml]")

    # read toml
    try:
        text_config = toml.load(sys.argv[1])
    except Exception as e:
        exit(e)

    # read the configuration
    config: satgen.config.Config = satgen.config.Config(text_config)

    # init the constellation
    constellation = satgen.constellation.Constellation(config)

    # prepare serializer
    serializer = satgen.json_serializer.Serializer()

    # prepare the state manager
    state_manager = satgen.state_manager.StateDiff(constellation, serializer)

    # run the simulation
    for i in range(0, config.simulation_steps):
        state_manager.step(config.resolution)

    # serialize the state
    serializer.persist()
