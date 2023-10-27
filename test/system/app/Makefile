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

.PHONY: all

all: validator.img

validator.img: validator.sh validator-base.sh validator.py
	@docker run --platform=linux/amd64 --rm -v $(PWD)/validator.py:/files/validator.py -v $(PWD)/validator.sh:/app.sh -v $(PWD)/validator-base.sh:/base.sh -v $(PWD):/opt/code --privileged rootfsbuilder $@
