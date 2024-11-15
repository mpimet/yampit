import xarray as xr

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
