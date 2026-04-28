import asyncio
import os
import traceback
from contextlib import suppress
from datetime import datetime
from typing import Any, Set

import websockets
from websockets.exceptions import ConnectionClosed

from config import get_source
from database import append_log, init_log
from telemetry import TelemetryService

HOST = "0.0.0.0"
PORT = 8765
FRAME_INTERVAL_S = 0.05
ERROR_RETRY_S = 0.5
PING_INTERVAL_S = 20
PING_TIMEOUT_S = 20

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ERROR_LOG = os.path.join(DATA_DIR, "backend_error.log")
MAX_ERROR_LOG_BYTES = 2_000_000  # ~2MB


def rotate_error_log() -> None:
    try:
        if os.path.exists(ERROR_LOG) and os.path.getsize(ERROR_LOG) > MAX_ERROR_LOG_BYTES:
            backup_path = ERROR_LOG + ".1"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(ERROR_LOG, backup_path)
    except OSError:
        # Logging should never take the server down.
        pass


def log_error(exc: BaseException, context: str = "backend error") -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    rotate_error_log()
    formatted = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    with open(ERROR_LOG, "a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.utcnow().isoformat()}] {context}: {repr(exc)}\n")
        handle.write(formatted + "\n")


class TelemetryServer:
    def __init__(self) -> None:
        self._telemetry = TelemetryService()
        self._clients: Set[Any] = set()

    async def register(self, websocket: Any) -> None:
        self._clients.add(websocket)

        latest = self._telemetry.latest_frame()
        if latest is None:
            return

        try:
            await websocket.send(latest.to_json())
        except ConnectionClosed:
            self._clients.discard(websocket)

    def unregister(self, websocket: Any) -> None:
        self._clients.discard(websocket)

    async def handler(self, websocket: Any) -> None:
        await self.register(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.unregister(websocket)

    async def broadcast(self, frame: dict) -> None:
        if not self._clients:
            return

        message = frame.to_json()
        clients = list(self._clients)
        results = await asyncio.gather(
            *(client.send(message) for client in clients),
            return_exceptions=True,
        )

        for client, result in zip(clients, results):
            if result is None:
                continue

            self.unregister(client)
            if not isinstance(result, ConnectionClosed):
                log_error(result, "failed to send telemetry frame")

    async def run_telemetry_loop(self) -> None:
        while True:
            try:
                frame = self._telemetry.next_frame()
                try:
                    append_log(frame)
                except Exception as exc:
                    log_error(exc, "telemetry database logging failed")
                await self.broadcast(frame)
                await asyncio.sleep(FRAME_INTERVAL_S)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log_error(exc, "telemetry loop failure")
                await asyncio.sleep(ERROR_RETRY_S)


async def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        init_log()
    except Exception as exc:
        log_error(exc, "telemetry database initialization failed")

    server = TelemetryServer()
    telemetry_task = asyncio.create_task(server.run_telemetry_loop())

    try:
        async with websockets.serve(
            server.handler,
            HOST,
            PORT,
            ping_interval=PING_INTERVAL_S,
            ping_timeout=PING_TIMEOUT_S,
            close_timeout=5,
            max_queue=32,
        ):
            print(f"WebSocket server running at ws://{HOST}:{PORT} (SOURCE={get_source()})")
            await asyncio.Future()
    finally:
        telemetry_task.cancel()
        with suppress(asyncio.CancelledError):
            await telemetry_task


if __name__ == "__main__":
    asyncio.run(main())
