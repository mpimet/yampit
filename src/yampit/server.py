from sanic import Sanic
from sanic.response import raw

import eccodes

from .catalog import demo
from .mapper import MarsDataset
from .async_polytope_request_handler import AsyncPolytopeRequestHandler

app = Sanic("YAMPIT_Server")

app.ctx.dataset = MarsDataset(**demo)
app.ctx.request_handler = AsyncPolytopeRequestHandler("polytope.lumi.apps.dte.destination-earth.eu", "destination-earth")

def is_meta(key):
    return key.split("/")[-1].startswith(".z")

@app.get("/ds/<key:path>")
async def get_chunk(request, key):
    kind, request = app.ctx.dataset.key2request(key)

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
        data = await app.ctx.request_handler.get(request)

        mid = eccodes.codes_new_from_message(data)
        data = eccodes.codes_get_array(mid, "values")
        eccodes.codes_release(mid)
        return raw(bytes(data.astype("<f4")), content_type=content_type, headers=headers)
    else:
        raise NotImplementedError(f"kind {kind}")
