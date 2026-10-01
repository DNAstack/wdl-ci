FROM python:3.14-slim-bookworm@sha256:c8137f4c460908c8763f281c8f22c431eb5c538514ba9553fc3a89c06b7cfb88

RUN apt-get -qq update \
	&& apt-get -qq install \
		git \
		wget \
		xz-utils \
		gcc \
		libffi-dev \
		build-essential

# Shellcheck
ENV SHELLCHECK_VERSION=v0.10.0
RUN wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${SHELLCHECK_VERSION}/shellcheck-${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" | tar -xJv --directory /opt
ENV PATH="${PATH}:/opt/shellcheck-${SHELLCHECK_VERSION}"

WORKDIR /usr/src

COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY src src

RUN python -m pip install --upgrade pip
RUN python -m pip install .

WORKDIR /usr/test

ENTRYPOINT [ "wdl-ci" ]
