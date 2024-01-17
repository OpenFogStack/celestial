#!/bin/sh

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

# check what chrony is doing
# now it should report the correct timesource
chronyc tracking

# ready to start the application!
# everything that is sent to stdout will be sent to our file
echo "STARTING VALIDATOR"

# let's get the gateway IP by parsing "/sbin/ip route"
IP=$(/sbin/ip route | awk '/default/ { print $3 }')

# the validation script should know where it can find the HTTP server
# (at our gateway)
python3 validator.py "$IP"

while true; do
    echo "$(date): satellite server running"
    sleep 60
done
