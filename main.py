import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import schedule
import time

import pandas as pd  # type: ignore

from src.modules.config_manager import ConfigManager
from src.modules.access_connector import AccessConnector
from src.modules.csv_exporter import CSVExporter
from src.modules.db import init_schema, get_last_sync, update_last_sync, get_connection


def setup_logging(level: str, log_file: str) -> None:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)


def extract_access_to_csv(
    incremental: bool = False,
    department: str | None = None,
    userid: str | None = None,
    username: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    cfg_mgr = ConfigManager()
    cfg_mgr.load()
    access = cfg_mgr.get_access_dsn()
    csv_cfg = cfg_mgr.get_csv_config()
    log_cfg = cfg_mgr.get_logging_config()

    setup_logging(log_cfg["level"], log_cfg["file"])
    init_schema()

    logging.info("Connexion à la base Access…")
    connector = AccessConnector(access["path"], access["driver"], access["timeout"], access.get("readonly", True))
    connector.connect()
    try:
        logging.info("Extraction des tables USERINFO, DEPARTMENTS, CHECKINOUT…")
        users = connector.get_users()
        deps = connector.get_departments()
        chk = connector.get_all_attendance()

        # Normalisation minimale
        users = users.rename(columns={"USERID": "userid", "Name": "username", "DEFAULTDEPTID": "dept_id"})
        deps = deps.rename(columns={"DEPTID": "dept_id", "DEPTNAME": "department"})
        chk = chk.rename(columns={"USERID": "userid", "CHECKTIME": "datetime", "CHECKTYPE": "status", "VERIFYCODE": "verify_code"})

        merged = chk.merge(users[["userid", "username", "dept_id"]], on="userid", how="left").merge(
            deps[["dept_id", "department"]], on="dept_id", how="left"
        )
        # Filtrage optionnel
        if start_date is not None:
            merged = merged[merged["datetime"] >= start_date]
        if end_date is not None:
            merged = merged[merged["datetime"] <= end_date]
        if department is not None:
            merged = merged[merged["department"] == department]
        if userid is not None:
            merged = merged[merged["userid"].astype(str) == str(userid)]
        if username is not None:
            merged = merged[merged["username"] == username]

        merged["device_id"] = None
        cols = ["userid", "username", "department", "datetime", "status", "device_id", "verify_code"]
        merged = merged[cols]

        exporter = CSVExporter(csv_cfg["output_directory"], csv_cfg["filename_pattern"])

        if incremental:
            conn = get_connection()
            try:
                last = get_last_sync(conn, device_id="ACCESS")
                if last:
                    logging.info(f"Export incrémental depuis {last}")
                    out = exporter.export_incremental(merged, since_date=last)
                else:
                    logging.info("Aucun last_sync, export complet initial")
                    out = exporter.export_full_data(merged)
                # Met à jour last_sync au max(datetime) exporté
                max_dt = str(merged["datetime"].max()) if not merged.empty else None
                update_last_sync(conn, last_sync=max_dt, total_records=len(merged), device_id="ACCESS")
            finally:
                conn.close()
        else:
            out = exporter.export_full_data(merged)
        logging.info(f"Export CSV créé: {out}")
        return out
    finally:
        connector.close_connection()


def run_scheduled_jobs() -> None:
    cfg_mgr = ConfigManager()
    cfg_mgr.load()
    csv_cfg = cfg_mgr.get_csv_config()
    log_cfg = cfg_mgr.get_logging_config()
    setup_logging(log_cfg["level"], log_cfg["file"])

    backup_time = csv_cfg.get("backup_time", "23:30")
    incremental = csv_cfg.get("auto_backup", True) and csv_cfg.get("incremental", True)

    def job():
        try:
            extract_access_to_csv(incremental=incremental)
            # Nettoyage rotation
            from src.modules.csv_exporter import CSVExporter

            exporter = CSVExporter(csv_cfg["output_directory"], csv_cfg["filename_pattern"])
            exporter.cleanup_old_files(days_to_keep=int(csv_cfg.get("keep_days", 365)))
        except Exception as e:
            logging.exception("Échec job planifié: %s", e)

    schedule.clear()
    schedule.every().day.at(backup_time).do(job)
    logging.info(f"Planification quotidienne à {backup_time} (incremental={incremental})")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # Exécution immédiate une fois (incremental), puis scheduler en arrière-plan
    extract_access_to_csv(incremental=True)
    run_scheduled_jobs()

