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

"""
Satgen generates satellite trajectories and network configurationfs for a
Celestial emulation run. It takes a TOML configuration file as an input
and generates a custom .zip format file as an output that contains changes
in network topologies at each time step.

To use satgen.py, you will need a full Celestial configuration file. Satgen
will check that the configuration file matches its expectations and will
exit with an error if it does not.

Prerequisites
-------------

Make sure you have all the necessary dependencies installed. You can install
them using pip in a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt



Usage
-----

    python3 satgen.py [config.toml] [output-file (optional)]

The output will be in the specified path or in a generated file based on a hash
of the configuration file if no output path is specified.
"""

import sys

import toml
import tqdm

import celestial.config
import celestial.zip_serializer
import celestial.satgen

if __name__ == "__main__":
    if len(sys.argv) > 3 or len(sys.argv) < 2:
        exit("Usage: python3 celestial.py [config.toml] [output-file (optional)]")

    # read toml
    try:
        text_config = toml.load(sys.argv[1])
    except Exception as e:
        exit(str(e))

    output_file = None
    if len(sys.argv) == 3:
        output_file = sys.argv[2]

    # read the configuration
    config: celestial.config.Config = celestial.config.Config(text_config)

    # prepare serializer
    # serializer = celestial.json_serializer.JSONSerializer(config)
    serializer = celestial.zip_serializer.ZipSerializer(config, output_file)

    # init the constellation
    constellation = celestial.satgen.SatgenConstellation(config, serializer)

    # run the simulation
    i = 0
    pbar = tqdm.tqdm(total=int(config.duration / config.resolution))
    while i < config.duration:
        # import cProfile

        # cProfile.run("constellation.step(i)", sort="cumtime")
        constellation.step(i)
        i += config.resolution
        pbar.update(1)

    # serialize the state
    serializer.persist()

    print(f"Output written to {serializer.filename}")
