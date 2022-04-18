---
layout: home
title: About
nav_order: 1
---

## About

Celestial is an emulator for the LEO edge.
It supports satellite servers as well as ground stations.
Each node is booted as a microVM.
Celestial scales across as many hosts as you want.

At any given time, only a subset of given satellite servers are booted,
dependent on your configured bounding box.

Celestial...

- ...creates Firecracker microVMs with your custom kernel and filesystem
- ...modifies network connections for a realistic network condition
- ...let's you define a bounding box on earth, so you only need to emulate
  satellites that you're actually interested in
- ...creates/suspends microVMs as they move in to/out of your bounding box
- ...has APIs for your satellites to retrieve some meta-information

Check out [`celestial-videoconferencing-evaluation`](https://github.com/OpenFogStack/celestial-videoconferencing-evaluation)
for an example application on Celestial!
Also check out the [`celestial-buoy-evaluation`](https://github.com/OpenFogStack/celestial-buoy-evaluation)
and the [`celestial-twissandra-evaluation`](https://github.com/OpenFogStack/celestial-twissandra-evaluation).
Even more examples can be found in [the `examples` directory](https://github.com/OpenFogStack/celestial/tree/main/examples).

**A word of caution**: you can technically run the server-side software on any
computer you want, but it requires root access to fiddle with your network settings.
Therefore, we _highly_ encourage you to only run it on dedicated servers.
It's doing its best to clean up everything, but it has to make changes to a lot
of networking settings, so we can't guarantee that it doesn't destroy any of your
other stuff.

### Research

If you use this software in a publication, please cite it as:

<div class="code-example" markdown="1">
T. Pfandzelter and D. Bermbach, **Celestial: Virtual Software System Testbeds
for the LEO Edge**, 23rd ACM/IFIP International Middleware Conference
(Middleware '22), Quebec City, Canada, 2022, doi: 10.1145/3528535.3531517.
</div>
```bibtex
@inproceedings{pfandzelter2022celestial,
    title = "Celestial: Virtual Software System Testbeds for the LEO Edge",
    booktitle = "23rd ACM/IFIP International Middleware Conference (Middleware '22)",
    author = "Pfandzelter, Tobias and Bermbach, David",
    year = 2022
}
```

A full list of our [publications](https://www.tu.berlin/en/mcc/research/publications/)
and [prototypes](https://www.tu.berlin/en/mcc/research/prototypes/)
is available on our group website.

### License

The code in this repository is licensed under the terms of the [GPLv3](./LICENSE)
license.

### Documentation

The complete documentation can be found at [`openfogstack.github.io/celestial`](https://openfogstack.github.io/celestial)
or in the `docs` directory.
