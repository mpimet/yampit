from sanic import Sanic, exceptions
from sanic.response import raw, json

import eccodes

from .catalog import read_destine_catalog, read_dmi_catalog
from .mapper import MarsDataset
from .async_polytope_request_handler import AsyncPolytopeRequestHandler
from .exceptions import NoSuchData

app = Sanic("YAMPIT_Server")

#app.ctx.datasets = {k: MarsDataset(**v) for k, v in read_destine_catalog().items()}
app.ctx.datasets = {k: MarsDataset(**v) for k, v in read_dmi_catalog().items()}
app.ctx.request_handler = AsyncPolytopeRequestHandler("polytope.lumi.apps.dte.destination-earth.eu", "destination-earth")

def is_meta(key):
    return key.split("/")[-1].startswith(".z")

@app.get("/ds")
async def list_datasets(request):
    return json(list(sorted(app.ctx.datasets)))

@app.get("/ds/<dsid>/<key:path>")
async def get_chunk(request, dsid, key):
    kind, request = app.ctx.datasets[dsid].key2request(key)

    if is_meta(key):
        content_type="application/json"
    else:
        content_type = "application/octet-stream"

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=604800",
    }

    if kind == 'inline':
        return raw(request, content_type=content_type, headers=headers)
    elif kind == 'request':
        try:
            data = await app.ctx.request_handler.get(request)
        except NoSuchData:
            raise exceptions.NotFound("Could not find data for MARS request " + str(request))

        mid = eccodes.codes_new_from_message(data)
        data = eccodes.codes_get_array(mid, "values")
        eccodes.codes_release(mid)
        return raw(bytes(data.astype("<f4")), content_type=content_type, headers=headers)
    else:
        raise NotImplementedError(f"kind {kind}")
