import xarray as xr
import numpy as np

icon_base_request = {
    "class": "d1",
    "dataset": "climate-dt",
    "activity": "CMIP6",
    "experiment": "hist",
    "generation": 1,
    "model": "ICON",
    "realization": 1,
    "resolution": "high",
    "expver": "0001",
    "type": "fc",
    "stream": "clte",
    "date": "19900101",
    "time": "0000",
    "param": 167,
    "levtype": "sfc",
    "step": 0,
}

npix = 12 * 4**10

hourly_atm2d = {
    "base_request": icon_base_request,
    "coords": {
        #"time": xr.date_range("1990-01-01T00:00", "2019-12-31T23:00", freq="1H"),
        "date": ["19910491"],
        "time": ["0100", "0200", "0300"],
        #"time": xr.date_range("1990-01-01T00:00", "2019-12-31T23:00", freq="1H"),
        "cell": np.arange(npix),
    },
    "variables": {
        str(varid): {"dims": ("date", "time", "cell")}
        for varid in [78, 79, 134, 137, 228164, 235, 260048, 146, 147, 169, 175, 176, 177, 178, 179, 140101, 140102, 130, 151, 165, 166, 167, 168, 260074]
    },
    "internal_dims": ["cell"],
}

demo_request = {
    'activity': 'ScenarioMIP',
    'class': 'd1',
    'dataset': 'climate-dt',
    'date': '20200102',
    'experiment': 'SSP3-7.0',
    'expver': '0001',
    'generation': '1',
    'levtype': 'sfc',
    'model': 'IFS-NEMO',
    'param': '134',
    'realization': '1',
    'resolution': 'standard',
    'stream': 'clte',
    'time': '0100', # '0100/0200/0300/0400/0500/0600'
    'type': 'fc'
}

demo = {
    "base_request": demo_request,
    "coords": {
        "time": ["0100", "0200"],
        "cell": np.arange(196608),
    },
    "variables": {
        "134": {"dims": ("time", "cell")},
        "165": {"dims": ("time", "cell")},
        "166": {"dims": ("time", "cell")},
    },
    "internal_dims": ["cell"],
}
