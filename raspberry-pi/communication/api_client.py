"""HTTPS client used to upload readings to the backend (secure device auth)."""
from __future__ import annotations

import time
from typing import Any

import requests

from config.settings import AUTH_TOKEN, BACKEND_URL, DEVICE_ID

TIMEOUT = 10


class APIClient:
    def __init__(self, backend_url: str = BACKEND_URL, token: str = AUTH_TOKEN) -> None:
        self.base_url = backend_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def register_device(self, name: str = "Raspberry Pi") -> None:
        try:
            requests.post(
                f"{self.base_url}/api/devices/register",
                json={"device_identifier": DEVICE_ID, "device_name": name},
                headers=self.headers,
                timeout=TIMEOUT,
            ).raise_for_status()
        except requests.RequestException as exc:
            print(f"Device registration failed: {exc}")

    def heartbeat(self) -> bool:
        """Notify the backend this device is alive (keeps status online)."""
        try:
            response = requests.post(
                f"{self.base_url}/api/devices/heartbeat",
                json={"device_identifier": DEVICE_ID, "device_name": "Raspberry Pi"},
                headers=self.headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            print(f"Heartbeat failed: {exc}")
            return False

    def upload(self, sample: dict) -> bool:
        payload = {"source": "pi", **sample}
        payload["device_id"] = None
        try:
            response = requests.post(
                f"{self.base_url}/api/sensor/readings",
                json=payload,
                headers=self.headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            print(f"Upload failed: {exc}")
            return False

    def upload_pending(self, samples: list[dict]) -> None:
        for sample in samples:
            if self.upload(sample):
                yield sample
            time.sleep(0.2)