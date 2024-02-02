---
layout: default
title: HTTP API
nav_order: 3
parent: Runtime
---

## HTTP API

First, an HTTP API lets your machines see information about the constellation and
about themselves.
For example, you may want to configure your application to do different things based
on the satellite it is deployed on.

To access the HTTP API, make an HTTP GET request to your microVM's gateway on port
80 (configurable).
We recommend simply using the `info.celestial` address.

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
  "identifier": {
    "id": 0,
    "name": "berlin"
  },
}
```

Returns (for a satellite):

```json
{
  "type": "sat",
  "active": true,
  "identifier": {
    "shell": 1,
    "id": 10,
  },
}
```

The `id` is the identifier of the machine within its shell.
`shell` is the identifier of its shell (the number within the configuration file
is used).
For ground stations, `shell` is `0`, `id` is the index within the configuration
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
  "shells": [
    {
      "sats": [
        {
          "type": "sat",
          "active": true,
          "identifier": {
            "shell": 1,
            "id": 0,
          },
        },
        {
          "type": "sat",
          "active": false,
          "identifier": {
            "shell": 1,
            "id": 2,
          },
        },
      ]
    }
  ],
  "groundstations": [
    {
      "type": "gst",
      "identifier": {
        "id": 0,
        "name": "berlin"
      },
    }
  ]
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
  "sats": [
    {
      "type": "sat",
      "active": true,
      "identifier": {
        "shell": 1,
        "id": 0,
      },
    },
    {
      "type": "sat",
      "active": false,
      "identifier": {
        "shell": 1,
        "id": 2,
      },
    },
  ]
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
  "type": "sat",
  "active": true,
  "identifier": {
    "shell": 1,
    "id": 10,
  },
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
  "type": "gst",
  "identifier": {
    "id": 0,
    "name": "berlin"
  },
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
  "source": {
    "id": 0,
    "name": "berlin",
  },
  "target": {
    "shell": 1,
    "id": 10,
  },
  "delay": 10000,
  "bandwidth": 10000,
  "blocked": false,
  "segments": [
    {
      "source":{
        "id": 0,
        "name": "berlin",
      },
      "target":{
        "shell": 1,
        "id": 9,
      },
      "delay": 4000,
      "bandwidth": 20000,
    },
    {
      "source":{
        "shell": 1,
        "id": 9,
      },
      "target":{
        "shell": 1,
        "id": 10,
      },
      "delay": 6000,
      "bandwidth": 10000,
    },
  ],
}
```

Note that `delay` is in microseconds and `bandwidth` in kbit/s.
