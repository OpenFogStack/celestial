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

.PHONY: all celestial peering database

all: celestial peering database

celestial peering database: ## Compile all proto files
	@protoc -I $@/ $@.proto --go_out=$@ --go_opt=paths=source_relative --go-grpc_out=$@ --go-grpc_opt=require_unimplemented_servers=false,paths=source_relative
	@python3 -m grpc_tools.protoc -I $@/ --python_out=$@ --grpc_python_out=$@ --mypy_out=$@ $@.proto