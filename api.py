"""Small asynchronous client for the legacy myJUDO cloud interface."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession

BASE_URL = "https://www.myjudo.eu/interface/"


class JudoCloudError(Exception):
    """Base exception."""


class JudoCloudAuthError(JudoCloudError):
    """Authentication failed."""


class JudoCloudConnectionError(JudoCloudError):
    """Communication failed."""


@dataclass(slots=True)
class JudoDevice:
    """Device returned by myJUDO."""

    index: int
    serial_number: str
    name: str
    raw: dict[str, Any]


def _register(registers: Any, index: int) -> str:
    """Return the hexadecimal data of a cloud register."""
    if isinstance(registers, list):
        entry = registers[index] if 0 <= index < len(registers) else None
    elif isinstance(registers, dict):
        entry = registers.get(str(index), registers.get(index))
    else:
        return ""
    return str(entry.get("data", "")) if isinstance(entry, dict) else ""


def _le_uint(value: str, byte_count: int = 4) -> int | None:
    """Decode an unsigned little-endian integer represented as hex."""
    try:
        raw = bytes.fromhex(value[: byte_count * 2])
        if len(raw) != byte_count:
            return None
        return int.from_bytes(raw, "little")
    except (TypeError, ValueError):
        return None


def _software_version(value: str) -> str | None:
    try:
        return f"{int(value[4:6], 16)}.{int(value[2:4], 16):02d}"
    except (TypeError, ValueError):
        return None


def _hardware_version(value: str) -> str | None:
    try:
        minor = int(value[0:2], 16)
        major = int(value[2:4], 16)
        return f"{major}.{minor:02d}"
    except (TypeError, ValueError):
        return None


def decode_device(raw_device: dict[str, Any]) -> dict[str, Any]:
    """Decode only the cloud values used by entities and device information."""
    data_sets = raw_device.get("data") or []
    block = data_sets[0] if data_sets and isinstance(data_sets[0], dict) else {}
    registers = block.get("data", {})

    return {
        "serial_number": str(raw_device.get("serialnumber", "")),
        "online": str(raw_device.get("status", "")).lower() in {"true", "online", "ok", "1"},
        "software_version": _software_version(_register(registers, 1)),
        "hardware_version": _hardware_version(_register(registers, 2)),
        "soft_water_total": _le_uint(_register(registers, 9)),
    }


class JudoCloudClient:
    """Client for myJUDO's legacy JSON endpoint."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._token: str | None = None

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.get(
                f"{BASE_URL}?{urlencode(params)}", timeout=60
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise JudoCloudConnectionError(str(err)) from err
        if not isinstance(payload, dict):
            raise JudoCloudConnectionError("Ungültige Antwort der JUDO-Cloud")
        return payload

    async def login(self) -> str:
        payload = await self._request(
            {
                "group": "register",
                "command": "login",
                "msgnumber": 1,
                "name": "login",
                "user": self._username,
                "password": md5(self._password.encode(), usedforsecurity=False).hexdigest(),
                "nohash": "Service",
                "role": "customer",
            }
        )
        if payload.get("status") not in ("online", "ok") or not payload.get("token"):
            raise JudoCloudAuthError(str(payload.get("data", "Login fehlgeschlagen")))
        self._token = str(payload["token"])
        return self._token

    async def devices(self, *, retry_login: bool = True) -> list[JudoDevice]:
        if not self._token:
            await self.login()
        payload = await self._request(
            {
                "token": self._token,
                "group": "register",
                "command": "get device data",
            }
        )
        if payload.get("status") not in ("online", "ok"):
            if retry_login:
                self._token = None
                await self.login()
                return await self.devices(retry_login=False)
            if payload.get("data") == "login failed":
                raise JudoCloudAuthError("Sitzung abgelaufen")
            raise JudoCloudConnectionError(str(payload.get("data", "Geräteabruf fehlgeschlagen")))
        raw_devices = payload.get("data")
        if not isinstance(raw_devices, list) or not raw_devices:
            raise JudoCloudConnectionError("Keine Geräte im JUDO-Konto gefunden")
        result = []
        for index, raw in enumerate(raw_devices):
            if not isinstance(raw, dict):
                continue
            serial = str(raw.get("serialnumber", index))
            result.append(JudoDevice(index, serial, f"JUDO {serial}", raw))
        return result

    async def start_regeneration(self, device_index: int, *, retry_login: bool = True) -> None:
        """Start regeneration using cloud register 65."""
        devices = await self.devices(retry_login=retry_login)
        if device_index < 0 or device_index >= len(devices):
            raise JudoCloudConnectionError("Das ausgewählte JUDO-Gerät wurde nicht gefunden")

        device = devices[device_index]
        data_sets = device.raw.get("data") or []
        block = data_sets[0] if data_sets and isinstance(data_sets[0], dict) else {}
        da = block.get("da")
        dt = block.get("dt")
        if da is None or dt is None:
            raise JudoCloudConnectionError("Geräteadresse fehlt in der Cloud-Antwort")

        payload = await self._request(
            {
                "token": self._token,
                "group": "register",
                "command": "write data",
                "serial_number": device.serial_number,
                "dt": dt,
                "index": 65,
                "data": "",
                "da": da,
                "role": "customer",
            }
        )
        if payload.get("data") == "login failed" and retry_login:
            self._token = None
            await self.login()
            return await self.start_regeneration(device_index, retry_login=False)
        if payload.get("status") in ("error", "failed", False):
            raise JudoCloudConnectionError(
                str(payload.get("data", "Regeneration konnte nicht gestartet werden"))
            )
