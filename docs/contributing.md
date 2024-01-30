---
layout: default
title: Contributing
nav_order: 2
---

## Contributing

Feel free to contribute to this project in any way you see fit.
Please note that all contributions must adhere to the terms of the GPLv3 license.

If you want to contribute code, please open a pull request on this GitHub repository.
Please make sure that your code passes the quality checks.
You can use [`act`](https://github.com/nektos/act) to run GitHub actions locally.

Most importantly, please check that `mypy` type checking completes without errors.
You can also use the tests in the [`test/`](https://github.com/OpenFogStack/celestial/blob/test)
directory to confirm that there are no regressions.

We include some tests for host-side code in the [`pkg/`](https://github.com/OpenFogStack/celestial/blob/pkg)
directory as well that can be run with `go test`.
