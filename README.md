# WDL Testing CLI
Tools to validate and test WDL-based repositories. To be used as part of CI/CD pipelines


install: `python -m pip install .`

run: `wdl-ci`

build docker image: `docker build -t wdl-testing-cli:latest .`

run docker container: `docker run wdl-testing-cli:latest`

run docker container (mount repo directory): `docker run -v ${PWD}:/usr/test wdl-testing-cli:latest`


## Linting with black

Install [black](https://github.com/psf/black), then run `git config core.hooksPath hooks/`.

`black` will be run on all python files as a pre-commit hook.
