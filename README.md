# function-xfabric

This function uses [Python][python], [Docker][docker], and the [Crossplane
CLI][cli] to build functions.

```shell
# Run the code in development mode, for crossplane render
hatch run development

# Lint and format the code - see pyproject.toml
hatch fmt

# Run unit tests - see tests/test_fn.py
hatch test

# Build the function's runtime image - see Dockerfile
$ docker build . --tag=runtime

# Build a function package - see package/crossplane.yaml
$ crossplane xpkg build -f package --embed-runtime-image=runtime
```

[python]: https://python.org
[docker]: https://www.docker.com
[cli]: https://docs.crossplane.io/latest/cli
