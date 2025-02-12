# YAMPIT
Builds datasets, jumps through FDBs.

`yampit` can present data served via MARS requests as a Zarr data store.
To do so, the dataset(s) must be defined in terms of some base mars request together with some information about how to construct variables and dimensions of that dataset.

## use as a library

You can use `yampit` as a library, meaning the translation between Zarr and a backend accepting MARS requests happens in the same process as your user code.
To do so, you'll need to configure a `yampit.Mapper` which does the translation and a `RequestHandler`, which handles exchanging MARS requests with a backend, e.g.:

```python
import xarray as xr
import zarr

from yampit import Mapper, PolytopeRequestHandler


mapper = Mapper(
    request_handler=PolytopeRequestHandler(
        "polytope.lumi.apps.dte.destination-earth.eu",
        "destination-earth",
    ),
    base_request={
        'activity': 'CMIP6',
        'class': 'd1',
        'dataset': 'climate-dt',
        'experiment': 'hist',
        'generation': '1',
        'levtype': 'sfc',
        'realization': '1',
        'resolution': 'high',
        'stream': 'clte',
        'type': 'fc',
    },
    coords={
        "time": xr.date_range("1991-03-01", "2012-12-31", freq="h"),
        "cell": range(12 * 4**10),
        "model": ["IFS-NEMO", "ICON"],
    },
    variables={
        "2t": {"dims": ("model", "time", "cell")},
        "tcwv": {"dims": ("model", "time", "cell")},
        "tclw": {"dims": ("model", "time", "cell")},
        "tclw": {"dims": ("model", "time", "cell")},
        "10u": {"dims": ("model", "time", "cell")},
        "10v": {"dims": ("model", "time", "cell")},
    },
    internal_dims=["cell"],
)

ds = xr.open_zarr(zarr.KVStore(mapper))
ds
```

## use as server

Alternatively, it's possible to run `yampit` as an HTTP-Web-Server.
In this case, the translation happens in the Server process and clients would connect to the server using HTTP.
From the client perspective, the Server would behave as if it would serve some static Zarr store.

This repository contains a docker compose file which can run a `yampit` server together with a varnish cache in front.
The configuration exposes one sample dataset from the DestinE platform.
In order to run it, you'll have to create the `docker/polytope.env` file based on `docker/polytope.env.dummy`.
The file has to contain your API key for the DestinE platfrom (e.g. as usually written in `~/.polytopeapirc`).
Afterwards, you can run the server from the `docker` folder using:

```bash
docker compose up
```

The dataset will be served at `127.0.0.1:2080/ds`, i.e. using Python, you can open it as:

```python
import xarray as xr
ds = xr.open_dataset("http://127.0.0.1:2080/ds", engine="zarr")
```
