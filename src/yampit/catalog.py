import numpy as np
import xarray as xr
import requests
from functools import lru_cache

demo = dict(
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

hpz7 = np.arange(12 * 4**7)
hpz9 = np.arange(12 * 4**9)
hpz10 = np.arange(12 * 4**10)
source_grids = {
    "hpz7-nested": hpz7,
    "hpz9-nested": hpz9,
    "hpz10-nested": hpz10,
    "icon-hpz10-nested": hpz10,
    "icon-hpz10-nested-3d": hpz10,
}

@lru_cache(maxsize=None)
def get_param_info(paramid):
    return requests.get(f"https://codes.ecmwf.int/parameter-database/api/v1/param/{paramid}/?format=json").json()

@lru_cache(maxsize=None)
def get_units():
    return {e["id"]: e["name"] for e in requests.get("https://codes.ecmwf.int/parameter-database/api/v1/unit/?format=json").json()}

def param_info_to_var_metadata(param_info):
    return {
        "id": param_info["id"],
        "attrs": {
            "long_name": param_info["name"],
            "units": get_units()[param_info["unit_id"]],
        }
    }

def convert_gsv_cat_entry(entry):
    args = entry["args"]
    metadata = entry["metadata"]
    if "levelist" in args["request"]:
        leveldim = {"levelist": np.array(args["request"]["levelist"])}
    else:
        leveldim = {}

    return {
        "base_request": {k: v for k, v in args["request"].items() if k not in ["levelist"]},
        "coords": {
            "time": xr.date_range(args["data_start_date"], args["data_end_date"], freq=args["savefreq"]),
            "cell": source_grids[metadata["source_grid_name"]],
            **leveldim,
        },
        "variables": {
            get_param_info(varid)["shortname"]: {
                "dims": ("time", *leveldim, "cell"),
                **param_info_to_var_metadata(get_param_info(varid)),
            }
            for varid in metadata["variables"]
        },
        "internal_dims": ["cell"],
    }

def _read_destine_catalog(url, prefix=None):
    import fsspec
    import yaml
    import jinja2
    from urllib.parse import urljoin


    catalog_dir = urljoin(url, '.')
    prefix = prefix or []
    with fsspec.open(url) as f:
        cat = yaml.safe_load(f)

    for name, config in cat.get("sources", {}).items():
        match config.get("driver"):
            case "gsv":
                try:
                    yield ".".join(prefix + [name]), convert_gsv_cat_entry(config)
                except Exception as e:
                    print("WARNING: could not read " + ".".join(prefix + [name]))
                    print(e)
            case "yaml_file_cat":
                cat_url = jinja2.Template(config["args"]["path"]).render(CATALOG_DIR=catalog_dir)
                yield from _read_destine_catalog(cat_url, prefix + [name])

def read_destine_catalog():
    root = "https://raw.githubusercontent.com/DestinE-Climate-DT/Climate-DT-catalog/refs/heads/main/catalogs/climatedt-phase1/catalog.yaml"
    return {name: config
            for name, config in _read_destine_catalog(root)}

def read_dmi_catalog():
    def format_param(varid):
        return {get_param_info(varid)["shortname"]: {"dims": ("time", "x", "y"), **param_info_to_var_metadata(get_param_info(varid))}}

    return {
        "deode_on_duty": {
            "base_request": {
                'class': 'd1',
                'dataset': 'on-demand-extremes-dt',
                'time': '0000',
                'expver': '0099',
                'date': '20241119',
                'levtype': 'sfc',
                'georef': 'ud3q9t',
                'stream': 'oper',
                'type': 'fc',
            },
            "coords":{
                "time": xr.date_range("2024-11-19", "2024-11-21", freq="h"),
                "x": range(1489),
                "y": range(1489),
            },
            "variables": {
                k: v
                for i in [167, 3073, 3074, 174096]
                for k, v in format_param(i).items()
            },
            "internal_dims": ["x", "y"],
        }
    }


if __name__ == "__main__":
    print(read_destine_catalog())
