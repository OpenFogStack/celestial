---
layout: default
title: HTTP API
parent: Services
grand_parent: Runtime
nav_order: 1
---

## HTTP API

First, an HTTP API lets your machines see information about the constellation and
about themselves.
For example, you may want to configure your application to do different things based
on the satellite it is deployed on.

To access the HTTP API, make an HTTP GET request to your microVM's gateway on port
80 (configurable).

### Self

```txt
  GET /self
```

Gets general information about self.
Requester is identified using their IP address.

Returns (for a ground station):

```json
{
  "type": "gst",
  "name": "berlin",
  "id": 0,
  "identifier": "berlin.gst.celestial"
}
```

Returns (for a satellite):

```json
{
  "type": "sat",
  "id": 1,
  "shell": 0,
  "identifier": "1.0.celestial"
}
```

The `id` is the identifier of the machine within its shell.
`shell` is the identifier of its shell (the index within the configuration file
is used).
For ground stations, `shell` is `-1`, `id` is the index within the configuration
file.
Here, the additional `name` parameter gives the name of the ground station.
For satellites, this is left empty.

### Info

```txt
  GET /info
```

Gets general information about constellation.

Returns:

```json
{
  "model": "Kepler",
  "shells": 2,
  "groundstations": [{ "name": "tester" }, { "name": "tester2" }]
}
```

### Get Shell Info

```txt
  GET /shell/${shell}
```

| Parameter | Type  | Description                           |
| :-------- | :---- | :------------------------------------ |
| `shell`   | `int` | **Required**. Index of shell to fetch |

Returns:

```json
{
  "planes": 6,
  "sats": 75,
  "altitude": 1325,
  "inclination": 70,
  "arcofascendingsnodes": 360,
  "eccentricity": 0,
  "activeSats": [
    { "shell": 0, "sat": 0 },
    { "shell": 0, "sat": 70 },
    { "shell": 0, "sat": 71 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 },
    { "shell": 0, "sat": 74 },
    { "shell": 0, "sat": 256 },
    { "shell": 0, "sat": 257 },
    { "shell": 0, "sat": 258 },
    { "shell": 0, "sat": 259 },
    { "shell": 0, "sat": 260 },
    { "shell": 0, "sat": 261 },
    { "shell": 0, "sat": 262 }
  ],
  "network": {
    "bandwidth": 10000000,
    "islpropagation": 0.000003336,
    "mincommsaltitude": 100000,
    "minelevation": 40.0,
    "gstpropagation": 0.000006672,
    "groundstationconnectiontype": "all"
  },
  "compute": {
    "vcpu": 1,
    "mem": 128,
    "disk": 20000,
    "ht": false,
    "kernel": "test.bin",
    "rootfs": "empty.img"
  }
}
```

### Get Satellite Info

```txt
  GET /shell/${shell}/${sat}
```

| Parameter | Type  | Description                               |
| :-------- | :---- | :---------------------------------------- |
| `shell`   | `int` | **Required**. Index of shell to fetch     |
| `sat`     | `int` | **Required**. Index of satellite to fetch |

Returns:

```json
{
  "position": { "x": 7689789, "y": 105726, "z": 290480 },
  "active": true,
  "connectedSats": [
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 }
  ],
  "connectedgst": [{ "name": "tester" }, { "name": "tester2" }]
}
```

### Get Ground Station Info

```txt
  GET /gst/${name}
```

| Parameter | Type     | Description                                   |
| :-------- | :------- | :-------------------------------------------- |
| `name`    | `string` | **Required**. Name of ground station to fetch |

Returns:

```json
{
  "position": { "x": 6296904, "y": 752587, "z": 611161 },
  "latitude": 5.504684,
  "longitude": 5.765499,
  "network": {
    "bandwidth": 10000000,
    "islpropagation": 0.000003336,
    "mincommsaltitude": 100000,
    "minelevation": 40.0,
    "gstpropagation": 0.000006672,
    "groundstationconnectiontype": "all"
  },
  "compute": {
    "vcpu": 2,
    "mem": 256,
    "disk": 5000,
    "ht": false,
    "kernel": "test.bin",
    "rootfs": "tester.img"
  },
  "connectedSats": [
    { "shell": 0, "sat": 0 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 },
    { "shell": 0, "sat": 74 },
    { "shell": 0, "sat": 258 },
    { "shell": 0, "sat": 259 },
    { "shell": 0, "sat": 260 },
    { "shell": 1, "sat": 77 },
    { "shell": 1, "sat": 78 }
  ]
}
```

### Get Path Info

```txt
  GET /path/${source_shell}/${source_sat}/${target_shell}/${target_sat}
```

| Parameter      | Type              | Description                                                                                       |
| :------------- | :---------------- | :------------------------------------------------------------------------------------------------ |
| `source_shell` | `int` or `"gst"`  | **Required**. Either ID of source shell or `gst` if ground station is desired.                    |
| `source_sat`   | `int` or `string` | **Required**. Either ID of source satellite or name of ground station if `source_shell` is `gst`. |
| `target`       | `int` or `"gst"`  | **Required**. Either ID of target shell or `gst` if ground station is desired.                    |
| `target_sat`   | `int` or `string` | **Required**. Either ID of target satellite or name of ground station if `target_shell` is `gst`. |

Returns:

```json
{
  "paths": [
    {
      "distance": 2385036,
      "delay": 15.91296,
      "bandwidth": 10000000,
      "segments": [
        {
          "sourceShell": -1,
          "sourceSat": 0,
          "targetShell": 0,
          "targetSat": 258,
          "delay": 11.612529,
          "distance": 1740487,
          "bandwidth": 10000000
        },
        {
          "sourceShell": -1,
          "sourceSat": 257,
          "targetShell": -1,
          "targetSat": 258,
          "delay": 2.1502154,
          "distance": 644549,
          "bandwidth": 10000000
        }
      ]
    }
  ]
}
```

This returns `-1` as a shell identifier for ground stations.
