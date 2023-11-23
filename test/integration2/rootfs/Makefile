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

all: ssh.img

ssh.img: ssh.sh ssh-base.sh id_ed25519.pub
	@docker run -it --platform=linux/amd64 --rm -v $(PWD)/ssh.sh:/app.sh -v $(PWD)/id_ed25519.pub:/files/id_ed25519.pub -v $(PWD)/ssh-base.sh:/base.sh -v $(PWD):/opt/code --privileged rootfsbuilder $@

id_ed25519.pub:
	cd .. ; ./make_key.sh
