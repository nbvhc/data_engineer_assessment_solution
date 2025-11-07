import os, hashlib
import mysql.connector as mysql
from dateutil.parser import parse as dtparse

def get_conn():
    return mysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        database=os.environ["MYSQL_DB"],
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        autocommit=False,
    )

def dict_get(d, dotted, default=None):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def coerce_date(s):
    if not s: return None
    try: return dtparse(s).date().isoformat()
    except: return None

def hash_key(parts):
    s = "|".join([str(p).strip().lower() if p is not None else "" for p in parts])
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_number(value):
    """
    Parse numeric value from various formats.
    Handles integers, floats, strings with numbers/units, and None/empty strings.
    Returns float, int, or None if parsing fails.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() == "null":
            return None
        import re
        cleaned = re.sub(r'[^\d.-]', '', value.replace(',', ''))
        if cleaned == "" or cleaned == "-" or cleaned == ".":
            return None
        try:
            result = float(cleaned)
            return int(result) if result.is_integer() else result
        except (ValueError, AttributeError):
            return None
    return None