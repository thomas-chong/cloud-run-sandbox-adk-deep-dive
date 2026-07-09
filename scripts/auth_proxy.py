#!/usr/bin/env python3
"""Local-only authenticated reverse proxy for a private Cloud Run ADK service."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def gcloud_token() -> str:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        fallback = Path("/usr/local/share/google-cloud-sdk/bin/gcloud")
        if not fallback.is_file():
            raise RuntimeError("gcloud CLI not found")
        gcloud = str(fallback)
    return subprocess.check_output(
        [gcloud, "auth", "print-identity-token"], text=True
    ).strip()


def create_app(target: str, token: str) -> FastAPI:
    app = FastAPI()
    client = httpx.AsyncClient(timeout=httpx.Timeout(300.0), follow_redirects=False)

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def proxy(path: str, request: Request) -> Response:
        url = f"{target.rstrip('/')}/{path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP and key.lower() != "authorization"
        }
        headers["authorization"] = f"Bearer {token}"
        upstream = await client.request(
            request.method,
            url,
            headers=headers,
            content=await request.body(),
        )
        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in HOP_BY_HOP
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=os.getenv("SERVICE_URL"))
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not args.target:
        parser.error("provide --target or SERVICE_URL")
    uvicorn.run(
        create_app(args.target, gcloud_token()),
        host="127.0.0.1",
        port=args.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
