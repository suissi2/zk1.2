from __future__ import annotations

from typing import Dict, Any, List, Optional

try:
    from zk import ZK, const  # type: ignore
except Exception:  # pragma: no cover
    ZK = None  # type: ignore
    const = None  # type: ignore


class ZKTecoManager:
    def __init__(self, devices_config: Dict[str, Dict[str, Any]]) -> None:
        self.devices_config = devices_config

    def _get_device(self, device_key: str) -> ZK:
        if ZK is None:
            raise RuntimeError("pyzk n'est pas installé")
        dev = self.devices_config[device_key]
        return ZK(dev["ip"], port=dev.get("port", 4370), timeout=5, password=dev.get("password", 0), force_udp=False, ommit_ping=False)

    def connect_device(self, device_key: str) -> Any:
        zk = self._get_device(device_key)
        conn = zk.connect()
        return conn

    def get_attendance_logs(self, device_key: str) -> List[Dict[str, Any]]:
        conn = self.connect_device(device_key)
        try:
            records = conn.get_attendance()
            out: List[Dict[str, Any]] = []
            for r in records or []:
                out.append(
                    {
                        "userid": getattr(r, "user_id", None),
                        "username": None,
                        "department": None,
                        "datetime": getattr(r, "timestamp", None),
                        "status": getattr(r, "status", None),
                        "device_id": self.devices_config[device_key]["ip"],
                        "verify_code": getattr(r, "punch", None),
                    }
                )
            return out
        finally:
            conn.disconnect()

    def sync_users(self, device_key: str) -> bool:
        conn = self.connect_device(device_key)
        try:
            users = conn.get_users()
            # Placeholder: à fusionner avec USERINFO si nécessaire
            return users is not None
        finally:
            conn.disconnect()

    def clear_attendance_logs(self, device_key: str) -> bool:
        conn = self.connect_device(device_key)
        try:
            conn.clear_attendance()
            return True
        finally:
            conn.disconnect()

    def get_device_info(self, device_key: str) -> Dict[str, Any]:
        conn = self.connect_device(device_key)
        try:
            return {
                "firmware": conn.get_firmware_version(),
                "serial": conn.get_serialnumber(),
                "platform": conn.get_platform(),
                "face_version": getattr(conn, "get_face_version", lambda: None)(),
            }
        finally:
            conn.disconnect()

