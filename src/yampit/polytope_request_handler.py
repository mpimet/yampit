import logging
import requests

class PolytopeRequestHandler:
    def __init__(self, server, collection):
        from polytope.api import Client
        self.client = Client(address=server)
        self.collection = collection

    def get(self, request):
        logging.getLogger("polytope.api").setLevel(logging.CRITICAL)

        pointer = self.client.retrieve(self.collection, request, pointer=True)
        data_url = pointer[0]["location"]
        request_id = data_url.split("/")[-1].split(".")[0]
        revoke_url = self.client.config.get_url("requests", request_id)

        headers = {"Authorization": ", ".join(self.client.auth.get_auth_headers())}

        try:
            r = requests.get(data_url)  # NOTE: data requests are unauthenticated
            r.raise_for_status()
            return r.content

        finally:
            r = requests.delete(revoke_url, headers=headers)
            r.raise_for_status()
