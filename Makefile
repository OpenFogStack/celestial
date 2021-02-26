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

.PHONY: build client server container binary runclient runserver installserver cleanupserver

build: proto container binary
client: proto container runclient
server: proto binary runserver

container: proto Dockerfile celestial.py celestial ## build client docker container
	docker build -t celestial .

binary: celestial.bin

celestial.bin: celestial.go pkg proto ## build go binary
	go build -o celestial.bin .

proto: ## build proto files
	cd ./proto ; make ; cd ..

runclient: container ## run client
	docker run --rm -it -v $(pwd)/config.toml:/config.toml celestial /config.toml

runserver: celestial.bin ## run server
	sudo ./celestial.bin

cleanupserver: ## run server cleanup
	bash ./cleanupserver.sh

installserver: ## install dependencies on server
	bash ./installserver.sh