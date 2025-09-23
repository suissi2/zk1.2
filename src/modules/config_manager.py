from configparser import ConfigParser
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    def __init__(self, config_path: str = "config.ini") -> None:
        self.config_path = Path(config_path)
        # Désactive l'interpolation pour permettre les patterns avec % (ex: %Y%m%d)
        self.parser = ConfigParser(interpolation=None)

    def load(self) -> ConfigParser:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Fichier de configuration introuvable: {self.config_path}")
        self.parser.read(self.config_path, encoding="utf-8")
        return self.parser

    def get_access_dsn(self) -> Dict[str, Any]:
        s = self.parser["ACCESS_DB"]
        return {
            "path": s.get("path"),
            "driver": s.get("driver", "Microsoft Access Driver (*.mdb, *.accdb)"),
            "timeout": s.getint("timeout", 30),
            "readonly": s.getboolean("readonly", True),
        }

    def get_csv_config(self) -> Dict[str, Any]:
        s = self.parser["CSV_EXPORT"]
        raw_out = s.get("output_directory", "./exports/")
        output_directory = os.path.expandvars(raw_out)
        return {
            "output_directory": output_directory,
            "filename_pattern": s.get("filename_pattern", "attendance_%Y%m%d_%H%M%S.csv"),
            "auto_backup": s.getboolean("auto_backup", True),
            "backup_time": s.get("backup_time", "23:30"),
        }

    def get_logging_config(self) -> Dict[str, Any]:
        s = self.parser["LOGGING"]
        return {"level": s.get("level", "INFO"), "file": s.get("file", "./logs/attendance_app.log")}

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        if "ZKTECO_DEVICES" not in self.parser:
            return {}
        s = self.parser["ZKTECO_DEVICES"]
        devices: Dict[str, Dict[str, Any]] = {}
        for key, value in s.items():
            if key.endswith("_ip"):
                prefix = key[:-3]
                devices[prefix] = {
                    "ip": value,
                    "port": s.getint(f"{prefix}_port", 4370),
                    "password": s.get(f"{prefix}_password", "0"),
                }
        return devices

