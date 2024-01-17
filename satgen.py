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

import sys

import toml
import tqdm

import celestial.config
import celestial.zip_serializer
import celestial.constellation

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
    constellation = celestial.constellation.Constellation(config, serializer)

    # run the simulation
    i = 0
    pbar = tqdm.tqdm(total=config.duration)
    while i < config.duration:
        constellation.step(i)
        i += config.resolution
        pbar.update(config.resolution)

    # serialize the state
    serializer.persist()

    print(f"Output written to {serializer.filename}")
