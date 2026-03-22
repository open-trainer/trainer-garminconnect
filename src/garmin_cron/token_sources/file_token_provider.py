from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..interfaces import ITokenProvider


class FileTokenProvider(ITokenProvider):
    """
    Resolve token sources from disk.

    Resolution strategy:
    1. If token_source is an absolute path -> use it.
    2. Otherwise try <tokens_dir>/<token_source> (tokenstore directory).
    3. If not found, try <tokens_dir>/<token_source>.json.
    """

    def __init__(self, tokens_dir: str) -> None:
        self.tokens_dir = Path(tokens_dir)

    def get_auth_payload(self, token_source: str) -> dict[str, Any]:
        source_path = Path(token_source)
        if source_path.is_absolute():
            path = source_path
        else:
            direct = self.tokens_dir / token_source
            with_json = self.tokens_dir / f"{token_source}.json"
            if direct.exists():
                path = direct
            elif with_json.exists():
                path = with_json
            else:
                path = direct

        if not path.exists():
            raise FileNotFoundError(f"Token source not found: {path}")

        if path.is_dir():
            return {
                "auth_type": "tokenstore",
                "tokenstore": str(path),
            }

        payload = json.loads(path.read_text(encoding="utf-8"))
        if "tokenstore" in payload:
            tokenstore = Path(payload["tokenstore"]).expanduser()
            if not tokenstore.is_absolute():
                tokenstore = (path.parent / tokenstore).resolve()
            return {"auth_type": "tokenstore", "tokenstore": str(tokenstore)}

        if "username" in payload and "password" in payload:
            return {
                "auth_type": "credentials",
                "username": payload["username"],
                "password": payload["password"],
            }

        raise ValueError(
            f"Token source {path} must contain either "
            "'username'+'password' or 'tokenstore'."
        )

