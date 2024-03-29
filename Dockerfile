FROM python:3.11.0-slim-buster

RUN apt-get -qq update \
	&& apt-get -qq install \
		git \
		shellcheck \
		gcc

WORKDIR /usr/src

COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY src src

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade psutil
RUN python -m pip install --upgrade click dnastack-client-library jsonpickle miniwdl requests
RUN python -m pip install .

WORKDIR /usr/test

ENTRYPOINT [ "wdl-ci" ]
