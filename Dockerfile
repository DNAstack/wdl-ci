FROM python:3.14-slim-bookworm@sha256:3fe1a0b6c2d6b2ebb572906cdabeca75aeb558c0c17db5ffefbcf8094871c32b

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
