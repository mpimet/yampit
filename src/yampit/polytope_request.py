async def get_http_client(**kwargs):
    import aiohttp
    return aiohttp.ClientSession(**kwargs)


class PolytopeRequest:
    def __init__(self, server, collection):
        from polytope.api import Client
        self.client = Client(address=server)
        self.collection = collection
        self._session = None
        self._get_http_client = get_http_client

    async def set_session(self):
        if self._session is None:
            self._session = await self._get_http_client()
        return self._session

    async def get(self, request):
        pointer = self.client.retrieve(self.collection, request, pointer=True)
        data_url = pointer[0]["location"]
        request_id = data_url.split("/")[-1].split(".")[0]
        revoke_url = self.client.config.get_url("requests", request_id)

        headers = {"Authorization": ", ".join(self.client.auth.get_auth_headers())}

        session = await self.set_session()

        try:
            async with session.get(data_url) as r:  # NOTE: data requests are unauthenticated
                r.raise_for_status()
                return await r.read()

        finally:
            async with session.delete(revoke_url, headers=headers) as r:
                r.raise_for_status()
