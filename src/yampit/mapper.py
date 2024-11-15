import json
import numpy as np
from functools import lru_cache

import eccodes

class MarsDataset:
    def __init__(self, base_request, coords, variables, internal_dims):
        self.base_request = base_request
        self.coords = {k: np.asarray(v) for k, v in coords.items()}
        self.variables = variables
        self.internal_dims = internal_dims
        
    def zmetadata(self):
        return json.dumps({
            "zarr_consolidated_format": 1,
            "metadata": {
                ".zattrs": {},
                ".zgroup": {
                    "zarr_format": 2
                },
                **{f"{name}/.zarray": {
                        "chunks": [len(var)],
                        "compressor": None,
                        "dtype": "i4" if name == "time" else var.dtype.descr[0][1],
                        "fill_value": None,
                        "filters": [],
                        "order": "C",
                        "shape": [len(var)],
                        "zarr_format": 2,
                    }
                    for name, var in self.coords.items()
                },
                **{f"{name}/.zattrs": {
                        "_ARRAY_DIMENSIONS": [name],
                        "units": f"seconds since {self.coords[name][0]}" if name == "time" else None,
                    }
                    for name, var in self.coords.items()
                },
                **{f"{name}/.zarray": {
                        "chunks": [len(self.coords[dim]) if dim in self.internal_dims else 1
                                   for dim in info["dims"]],
                        "compressor": None,
                        "dtype": "<f4",
                        "fill_value": None,
                        "filters": [],
                        "order": "C",
                        "shape": [len(self.coords[dim]) for dim in info["dims"]],
                        "zarr_format": 2,
                    }
                    for name, info in self.variables.items()
                },
                **{f"{name}/.zattrs": {
                        "_ARRAY_DIMENSIONS": list(info["dims"]),
                    }
                    for name, info in self.variables.items()
                },
            }
        }).encode("utf-8")

    def coord(self, name):
        if name == "time":
            return bytes((self.coords[name] - self.coords[name][0]).astype("timedelta64[s]").astype(np.int32))
        else:
            return bytes(self.coords[name])

    def key2request(self, key):
        if key == ".zmetadata":
            return 'inline', self.zmetadata()

        var, chunk = key.split("/")
        chunk = list(map(int, chunk.split(".")))

        if var in self.coords:
            return 'inline', self.coord(var)

        def _encode_mars_request(dim, c):
            if dim == "time":
                date_str = np.datetime_as_string(c, "m")
                date, time = date_str.replace("-", "").replace(":", "").split("T")

                return {"date": date, "time": time}
            else:
                return {dim: str(c)}

        return 'request', {
            **self.base_request,
            "param": var,
            **{
                k: v
                for dim, idx in zip(self.variables[var]["dims"], chunk)
                if dim not in self.internal_dims
                for k, v in _encode_mars_request(dim, self.coords[dim][idx]).items()
            }
        }


class Mapper:
    def __init__(self, request_handler, *args, **kwargs):
        self.request_handler = request_handler
        self._mds = MarsDataset(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @lru_cache
    def __getitem__(self, key):
        kind, request = self._mds.key2request(key)

        if kind == 'inline':
            return request
        elif kind == 'request':
            self.logger.debug("requesting %s for %s", request, key)
            data = self.request_handler.get(request)
            mid = eccodes.codes_new_from_message(data)
            data = eccodes.codes_get_array(mid, "values")
            eccodes.codes_release(mid)
            return bytes(data.astype("<f4"))
        else:
            raise NotImplementedError(f"kind {kind}")

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False
