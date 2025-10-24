import json
import logging
from urllib.parse import urljoin
import aiohttp
import asyncio


logger = logging.getLogger(__name__)


async def get_client(**kwargs):
    return aiohttp.ClientSession(**kwargs)


class AsyncPolytopeRequestHandler:
    def __init__(self, server, collection):
        from polytope.api import Client
        self.client = Client(address=server)

        self.server = server
        self.collection = collection
        self.get_client = get_client
        self.max_poll_retries = 100
        self._session = None

        self.auth_headers = {"Authorization": ", ".join(self.client.auth.get_auth_headers())}


    async def set_session(self):
        if self._session is None:
            self._session = await self.get_client()
        return self._session

    def __del__(self):
        if self._session:
            self._session.close()

    async def _poll_get(self, url):
        session = await self.set_session()

        for i in range(self.max_poll_retries):
            async with session.get(url, headers=self.auth_headers) as r:
                r.raise_for_status()
                match r.status:
                    case 200:  # OK, direct download
                        return await r.read()
                    case 202:  # Accepted, scheduled. Needs polling
                        url = urljoin(url, r.headers.get("Location"))
                        wait = int(r.headers.get("Retry-After", 0))
                        await asyncio.sleep(wait)
                        continue
                    case 303:  # redirect to direct download
                        raise NotImplementedError("direct download")
        else:
            raise RuntimeError("max poll retries exceeded")


    async def get(self, request):
        request_object = {"verb": "retrieve", "request": json.dumps(request)}
        url = self.client.config.get_url("requests", collection_id=self.collection)
        poll_url = None

        session = await self.set_session()
        async with session.post(url, headers=self.auth_headers, json=request_object) as r:
            r.raise_for_status()
            match r.status:
                case 200:  # OK, direct download
                    res = await r.read()
                case 202:  # Accepted, scheduled. Needs polling
                    poll_url = urljoin(url, r.headers.get("Location"))
                    wait = int(r.headers.get("Retry-After", 0))
                    await asyncio.sleep(wait)
                    res = await self._poll_get(poll_url)
                case 303:  # redirect to direct download
                    raise NotImplementedError("direct download")

        if poll_url:
            async with session.delete(poll_url, headers=self.auth_headers) as r:
                if not r.ok:
                    logger = logging.getLogger(__name__)
                    logger.warn("couldn't DELETE %s: %s %s", revoke_url, r.status_code, r.reason)
        return res
