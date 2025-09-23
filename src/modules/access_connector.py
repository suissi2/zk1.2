from typing import Optional
import shutil
from pathlib import Path
import pyodbc  # type: ignore
import pandas as pd  # type: ignore


class AccessConnector:
    def __init__(self, db_path: str, driver: str = "Microsoft Access Driver (*.mdb, *.accdb)", timeout: int = 30, readonly: bool = True) -> None:
        self.db_path = db_path
        self.driver = driver
        self.timeout = timeout
        self.readonly = readonly
        self.conn: Optional[pyodbc.Connection] = None
        self._db_effective_path: Optional[str] = None

    def connect(self) -> bool:
        ro = ";READONLY=TRUE;Exclusive=0" if self.readonly else ";Exclusive=0"
        self._db_effective_path = self.db_path
        conn_str = f"DRIVER={{{self.driver}}};DBQ={self._db_effective_path}{ro};"
        self.conn = pyodbc.connect(conn_str, timeout=self.timeout)
        return True

    def close_connection(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _read_table(self, table: str) -> pd.DataFrame:
        if self.conn is None:
            raise RuntimeError("Connexion Access non initialisée")
        query = f"SELECT * FROM {table}"
        try:
            return pd.read_sql(query, self.conn)
        except Exception as exc:
            msg = str(exc)
            # Fallback en cas de verrouillage: copier MDB en local et relire
            if "déjà ouverte en mode exclusif" in msg or "already opened exclusively" in msg or "-1302" in msg:
                # Copier vers data/cache
                src = Path(self.db_path)
                cache_dir = Path("data/cache")
                cache_dir.mkdir(parents=True, exist_ok=True)
                dst = cache_dir / (src.name if src.name else "ATT2000_copy.mdb")
                try:
                    shutil.copy2(self.db_path, dst)
                except Exception:
                    raise
                # Reconnecter sur la copie
                if self.conn is not None:
                    try:
                        self.conn.close()
                    except Exception:
                        pass
                ro = ";READONLY=TRUE;Exclusive=0" if self.readonly else ";Exclusive=0"
                self._db_effective_path = str(dst)
                conn_str = f"DRIVER={{{self.driver}}};DBQ={self._db_effective_path}{ro};"
                self.conn = pyodbc.connect(conn_str, timeout=self.timeout)
                return pd.read_sql(query, self.conn)
            raise

    def get_all_attendance(self) -> pd.DataFrame:
        return self._read_table("CHECKINOUT")

    def get_users(self) -> pd.DataFrame:
        return self._read_table("USERINFO")

    def get_departments(self) -> pd.DataFrame:
        return self._read_table("DEPARTMENTS")

    def get_holidays(self) -> pd.DataFrame:
        return self._read_table("HOLIDAYS")

    def get_user_speday(self) -> pd.DataFrame:
        return self._read_table("USER_SPEDAY")

    def get_attendance_by_date(self, start_date: str, end_date: str) -> pd.DataFrame:
        if self.conn is None:
            raise RuntimeError("Connexion Access non initialisée")
        # Les dates Access utilisent #YYYY-MM-DD HH:MM:SS#
        query = (
            "SELECT * FROM CHECKINOUT WHERE CHECKTIME >= ? AND CHECKTIME <= ?"
        )
        return pd.read_sql(query, self.conn, params=[start_date, end_date])

