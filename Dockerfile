FROM python:3.11.0-slim-buster

RUN apt-get -qq update \
	&& apt-get -qq install \
		git \
		wget \
		xz-utils \
		gcc

# Shellcheck
ENV SHELLCHECK_VERSION=v0.10.0
RUN wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${SHELLCHECK_VERSION}/shellcheck-${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" | tar -xJv --directory /opt
ENV PATH="${PATH}:/opt/shellcheck-${SHELLCHECK_VERSION}"

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
