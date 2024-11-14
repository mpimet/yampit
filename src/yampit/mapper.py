import json
import numpy as np
from functools import lru_cache

import eccodes

class Mapper:
    def __init__(self, request_handler, base_request, coords, variables, internal_dims):
        self.request_handler = request_handler
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
                        "dtype": var.dtype.descr[0][1],
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
        return bytes(self.coords[name])

    @lru_cache
    def __getitem__(self, key):
        print(key)
        if key == ".zmetadata":
            return self.zmetadata()
        try:
            var, chunk = key.split("/")
            chunk = list(map(int, chunk.split(".")))
        except KeyError:
            raise KeyError()

        if var in self.coords:
            return self.coord(var)
        request = {
            **self.base_request,
            "param": var,
            **{dim: str(self.coords[dim][idx])
               for dim, idx in zip(self.variables[var]["dims"], chunk)
               if dim not in self.internal_dims}
        }

        print(request)
        
        data = self.request_handler.get(request)
        mid = eccodes.codes_new_from_message(data)
        data = eccodes.codes_get_array(mid, "values")
        eccodes.codes_release(mid)
        return bytes(data.astype("<f4"))

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False
