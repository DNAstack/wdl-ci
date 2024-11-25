FROM python:3.11.0-slim-buster

RUN apt-get -qq update \
	&& apt-get -qq install \
		git \
		wget \
		xz-utils \
		gcc

# Set all ENV variables
ENV SHELLCHECK_VERSION=v0.10.0 \
  PIP_VERSION=24.3.1 \
  CLICK_VERSION=8.1.7 \
  PSUTIL_VERSION=6.1.0 \
  DNASTACK_CLIENT_LIBRARY_VERSION=3.1.59 \
  JSONPICKLE_VERSION=4.0.0 \
  MINIWDL_VERSION=1.12.1 \
  REQUESTS_VERSION=2.32.3

# Shellcheck
RUN wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${SHELLCHECK_VERSION}/shellcheck-${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" | tar -xJv --directory /opt
ENV PATH="${PATH}:/opt/shellcheck-${SHELLCHECK_VERSION}"

WORKDIR /usr/src

COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY src src

RUN python -m pip install --upgrade pip==${PIP_VERSION}
RUN python -m pip install --upgrade psutil==${PSUTIL_VERSION}
RUN python -m pip install --upgrade click==${CLICK_VERSION} dnastack-client-library==${DNASTACK_CLIENT_LIBRARY_VERSION} jsonpickle==${JSONPICKLE_VERSION} miniwdl==${MINIWDL_VERSION} requests==${REQUESTS_VERSION}
RUN python -m pip install .

WORKDIR /usr/test

ENTRYPOINT [ "wdl-ci" ]
