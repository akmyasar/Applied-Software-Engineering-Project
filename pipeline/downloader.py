import time
import requests
from pathlib import Path

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "QDArchive-Seeder/1.0 (FAU Erlangen; student 23025328)"})

def download_file(url, dest_path, api_token=None):
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    params = {}
    if api_token:
        params["key"] = api_token
    try:
        resp = SESSION.get(url, params=params, stream=True, timeout=60)
    except requests.exceptions.ConnectionError:
        return "FAILED_SERVER_UNRESPONSIVE", 0
    except requests.exceptions.Timeout:
        return "FAILED_SERVER_UNRESPONSIVE", 0
    if resp.status_code in (401, 403):
        return "FAILED_LOGIN_REQUIRED", 0
    if resp.status_code != 200:
        return "FAILED_SERVER_UNRESPONSIVE", 0
    content_length = int(resp.headers.get("Content-Length", 0))
    if content_length > MAX_FILE_SIZE_BYTES:
        return "FAILED_TOO_LARGE", 0
    bytes_written = 0
    try:
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                bytes_written += len(chunk)
                if bytes_written > MAX_FILE_SIZE_BYTES:
                    fh.close()
                    dest_path.unlink(missing_ok=True)
                    return "FAILED_TOO_LARGE", 0
                fh.write(chunk)
    except OSError as exc:
        print(f"    [WARN] OS error: {exc}")
        return "FAILED_SERVER_UNRESPONSIVE", 0
    return "SUCCEEDED", bytes_written

def polite_sleep(seconds=1.0):
    time.sleep(seconds)
