import base64
import requests
from src.utils.config_reader import load_config
from src.utils.logger import logger


class TigerGraphClient:
    def __init__(self, market: str):
        config = load_config(market)
        tg_cfg = config["TIGERGRAPH"]

        host = tg_cfg["host"]
        rest_port = tg_cfg.get("rest_port", "9000")
        gsql_port = tg_cfg.get("gsql_port", "14240")  #GSQL port
        self.graph_name = tg_cfg["graph_name"]

        # NEW — load username & password from config.ini
        self.username = tg_cfg.get("username")
        self.password = tg_cfg.get("password")

        self.rest_base_url = f"http://{host}:{rest_port}"    # for /echo or run installed queries etc
        self.gsql_base_url = f"http://{host}:{gsql_port}"    # to run raw gsql, schema change, compile query etc


        self.headers = {}  # no Bearer token for TigerGraph

        if self.username and self.password:
                    raw = f"{self.username}:{self.password}"
                    basic_token = base64.b64encode(raw.encode()).decode()
                    self.auth_header = {"Authorization": f"Basic {basic_token}"}    # we require username n password so we need tht.
        else:
            logger.warning(
                "TIGERGRAPH CLIENT INIT - username/password not set in config; "
                "GSQL endpoints will return 401."
            )

        logger.info(
            "TIGERGRAPH CLIENT INIT - host=%s rest_port=%s gsql_port=%s graph=%s",
            host,
            rest_port,
            gsql_port,
            self.graph_name,
        )


#This is just a health check to confirm: TigerGraph is reachable and responding.
    def ping(self):
        url = f"{self.rest_base_url}/echo"

        headers = {
            "Content-Type": "application/json",
            **self.auth_header, 
        }

        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


    def run_interpret_query(self, gsql: str):
        url = f"{self.gsql_base_url}/gsql/v1/queries/interpret"  #api expects plain text 
        headers = {
            "Content-Type": "text/plain",
            **self.auth_header   # if we dont gv auth then , TigerGraph immediately rejects the request with 401 Unauthorized
        }

        resp = requests.post(url, data=gsql, headers=headers)
        resp.raise_for_status()
        return resp.json() #parsing , buil in fucntion in python
