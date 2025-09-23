from __future__ import annotations

import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore


class CSVExporter:
    def __init__(self, output_dir: str, filename_pattern: str = "attendance_%Y%m%d_%H%M%S.csv") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filename_pattern = filename_pattern

    def _timestamped_path(self, suffix: str = ".csv") -> Path:
        ts_name = datetime.now().strftime(self.filename_pattern)
        path = self.output_dir / ts_name
        if not str(path).endswith(suffix):
            path = Path(str(path) + suffix)
        return path

    def export_full_data(self, data: pd.DataFrame) -> str:
        cols = [
            "userid",
            "username",
            "department",
            "datetime",
            "status",
            "device_id",
            "verify_code",
        ]
        df = data.copy()
        missing = [c for c in cols if c not in df.columns]
        for c in missing:
            df[c] = None
        df = df[cols]
        out_path = self._timestamped_path(".csv")
        df.to_csv(out_path, index=False, encoding="utf-8")
        # Compression si gros fichier (>25MB)
        if out_path.stat().st_size > 25 * 1024 * 1024:
            self._gzip_file(out_path)
        return str(out_path)

    def export_incremental(self, data: pd.DataFrame, since_date: str) -> str:
        df = data.copy()
        if "datetime" in df.columns:
            df = df[df["datetime"] >= since_date]
        return self.export_full_data(df)

    def create_backup(self, source_file: Optional[str] = None) -> str:
        # archive mensuelle/quotidienne par défaut
        if source_file is None:
            # crée un CSV vide nommé backup timestampé
            out_path = self._timestamped_path(".backup.csv")
            out_path.write_text("userid,username,department,datetime,status,device_id,verify_code\n", encoding="utf-8")
        else:
            out_path = self.output_dir / (Path(source_file).name + ".bak")
            Path(source_file).replace(out_path)
        # compresse
        self._gzip_file(out_path)
        return str(out_path) + ".gz"

    def cleanup_old_files(self, days_to_keep: int) -> None:
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        for p in self.output_dir.iterdir():
            try:
                if p.is_file() and datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                    p.unlink()
            except Exception:
                continue

    def _gzip_file(self, path: Path) -> None:
        gz_path = Path(str(path) + ".gz")
        with open(path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            f_out.writelines(f_in)
        try:
            path.unlink()
        except Exception:
            pass

