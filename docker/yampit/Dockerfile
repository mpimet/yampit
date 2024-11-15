FROM python:3.12-slim-bookworm
RUN apt update && apt install -y git cmake gcc g++ gfortran

ARG eccodes_version=2.38.3
RUN mkdir -p /src
WORKDIR /src
#RUN git clone https://github.com/ecmwf/ecbuild --depth 1 -b $ecbuild_version
#ENV PATH="${PATH}:/src/ecbuild/bin"
RUN git clone https://github.com/ecmwf/eccodes --depth 1 -b $eccodes_version
RUN apt install -y libaec-dev
RUN mkdir /src/eccodes/build && cd /src/eccodes/build && cmake .. -DENABLE_AEC=ON && make && make install

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir /app
ADD README.md src pyproject.toml uv.lock /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
#RUN uv build
RUN uv sync --frozen

# use POLYTOPE_USER_KEY environment variable to authenticate against polytope server
CMD ["uv", "run", "sanic", "yampit.server", "-H0.0.0.0"]
