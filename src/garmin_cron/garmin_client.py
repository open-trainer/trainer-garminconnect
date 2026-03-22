from __future__ import annotations

from typing import Any

from garminconnect import Garmin


class GarminClientFactory:
    def create(self, auth_payload: dict[str, Any]) -> Garmin:
        auth_type = auth_payload.get("auth_type")
        if auth_type == "tokenstore":
            tokenstore = auth_payload["tokenstore"]
            api = Garmin()
            api.login(tokenstore)
            return api

        if auth_type == "credentials":
            api = Garmin(auth_payload["username"], auth_payload["password"])
            api.login()
            return api

        raise ValueError(f"Unsupported auth payload type: {auth_type}")

