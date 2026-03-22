from __future__ import annotations

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv
from garth.exc import GarthException, GarthHTTPError
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Authenticate to Garmin Connect and persist tokens for cron reuse."
    )
    parser.add_argument(
        "--token-source",
        required=True,
        help=(
            "Token source name (for example user id). "
            "Tokens are stored in <tokens-dir>/<token-source>/."
        ),
    )
    parser.add_argument("--tokens-dir", default=os.getenv("TOKENS_DIR", "tokens"))
    parser.add_argument("--email", default=os.getenv("EMAIL"))
    parser.add_argument("--password", default=os.getenv("PASSWORD"))
    parser.add_argument("--is-cn", action="store_true", help="Use Garmin China endpoint.")
    return parser


def resolve_tokenstore(tokens_dir: str, token_source: str) -> Path:
    source = Path(token_source)
    if source.is_absolute():
        return source
    return Path(tokens_dir) / token_source


def get_credentials(email: str | None, password: str | None) -> tuple[str, str]:
    if not email:
        email = input("Login email: ").strip()
    if not password:
        password = getpass("Password: ")
    return email, password


def login_with_tokenstore(tokenstore: Path) -> Garmin | None:
    if not tokenstore.exists():
        return None
    try:
        api = Garmin()
        api.login(str(tokenstore))
        return api
    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarthHTTPError,
    ):
        return None


def login_interactive(
    email: str,
    password: str,
    tokenstore: Path,
    is_cn: bool,
) -> Garmin:
    while True:
        try:
            api = Garmin(
                email=email,
                password=password,
                is_cn=is_cn,
                return_on_mfa=True,
            )
            login_status, login_state = api.login()
            if login_status == "needs_mfa":
                mfa_code = input("MFA code: ").strip()
                api.resume_login(login_state, mfa_code)

            tokenstore.mkdir(parents=True, exist_ok=True)
            api.garth.dump(str(tokenstore))
            return api
        except GarminConnectAuthenticationError:
            print("Authentication failed. Try credentials again.")
            email, password = get_credentials(None, None)
        except GarthHTTPError as error:
            if "429" in str(error):
                raise GarminConnectTooManyRequestsError(str(error)) from error
            raise
        except GarthException as error:
            print(f"Login state error: {error}. Try MFA again.")


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()
    tokenstore = resolve_tokenstore(args.tokens_dir, args.token_source)

    try:
        api = login_with_tokenstore(tokenstore)
        if api:
            print(f"Token login successful: {tokenstore}")
            return 0

        email, password = get_credentials(args.email, args.password)
        api = login_interactive(
            email=email,
            password=password,
            tokenstore=tokenstore,
            is_cn=args.is_cn,
        )
        if api:
            print(f"Token login successful: {tokenstore}")
            return 0
        return 1
    except GarminConnectTooManyRequestsError as error:
        print(f"Too many requests: {error}")
        return 1
    except GarminConnectConnectionError as error:
        print(f"Connection error: {error}")
        return 1
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    except Exception as error:
        print(f"Failed to authenticate: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

