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

.PHONY: all

all: app/validator.img satgen.zip

app/validator.img: app/validator.sh app/validator-base.sh app/validator.py
	@docker run --platform=linux/amd64 --rm -v $(PWD)/app/validator.py:/files/validator.py -v $(PWD)/app/validator.sh:/app.sh -v $(PWD)/app/validator-base.sh:/base.sh -v $(PWD):/opt/code --privileged rootfsbuilder $@

satgen.zip: config.toml
	cd ../.. && source .venv/bin/activate && python3 satgen.py test/system/$< test/system/$@ && deactivate
