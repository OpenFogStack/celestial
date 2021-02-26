# Celestial: Examples

We provide two example applications for Celestial to help you get started.

## Animation Only

If you would like to animate a satellite constellation, use the `animate.py`
program in the root of the repository like so:

```sh
python3 animate.py ./path/to/configuration.toml
```

In the [`animation`](./animation) directory, you can find two example
configuration files.

`starlink.toml` has all parameters for the complete Starlink phase I
constellation, so use that to animate that constellation.

`geostationary.toml` has a single geo-stationary satellite in orbit
around earth.

## Validator

We use the validator to check that simulated network distances are accurately
reflected in Celestial.

The included Python3 program runs on a ground station server and measures
network latency to a selection of satellites using the `ping3` library.
Deploy it on a Celestial testbed and pull the resulting `validate.csv` file.
You can use our `validate.ipynb` notebook to analyze results and check whether
expected network distances match measurements (they should).
