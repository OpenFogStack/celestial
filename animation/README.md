# Animation Only

If you would like to animate a satellite constellation, use the `animate.py`
program in the root of the repository:

```sh
python3 animate.py ./path/to/configuration.toml
```

![Constellation Animation](../docs/assets/celestial-constellation.gif)

In the [`animation`](./animation) directory, you can find multiple example
configuration files.

`starlink.toml` has all parameters for the complete Starlink constellation, so
use that to animate that constellation:

```sh
# in /celestial root directory
python3 animate.py ./animation/starlink.toml
```

`geostationary.toml` has a single geostationary satellite in orbit
around earth.
