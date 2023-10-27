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

ARCH=amd64
OS=linux

.PHONY: build container celestial-make rootfsbuilder

build: proto/ celestial.bin

container: proto Dockerfile celestial.py celestial ## build client docker container
	docker build -t celestial .

celestial.bin: go.mod go.sum celestial.go pkg/ proto/ ## build go binary
	GOOS=${OS} GOARCH=${ARCH} go build -o celestial.bin .

proto/: ## build proto files
	cd ./proto ; make ; cd ..

celestial-make: ## build the compile container
	docker build --platform ${OS}/${ARCH} -f compile.Dockerfile -t celestial-make .

rootfsbuilder: ## build the rootfs builder container
	cd ./builder ; make rootfsbuilder ; cd ..
