import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SOURCE_URL = os.environ.get("RELAY_SOURCE_URL", "").rstrip("/")
RELAY_TOKEN = os.environ.get("NOTIFICATION_RELAY_TOKEN", "")
NAPCAT_API_URL = os.environ.get("NAPCAT_API_URL", "http://127.0.0.1:3000").rstrip("/")
NAPCAT_GROUP_ID = os.environ.get("NAPCAT_GROUP_ID", "")
NAPCAT_ACCESS_TOKEN = os.environ.get("NAPCAT_ACCESS_TOKEN", "")
POLL_INTERVAL = float(os.environ.get("RELAY_POLL_INTERVAL", "5"))
REQUEST_TIMEOUT = float(os.environ.get("RELAY_REQUEST_TIMEOUT", "10"))


def main():
    validate_config()
    print("NapCat relay started.")
    print(f"Source: {SOURCE_URL}")
    print(f"NapCat: {NAPCAT_API_URL}")
    print(f"Group: {NAPCAT_GROUP_ID}")

    while True:
        try:
            notifications = fetch_notifications()
            for notification in notifications:
                process_notification(notification)
        except KeyboardInterrupt:
            print("NapCat relay stopped.")
            return
        except Exception as exc:
            print(f"Relay loop failed: {exc}", file=sys.stderr)
        time.sleep(POLL_INTERVAL)


def validate_config():
    missing = []
    if not SOURCE_URL:
        missing.append("RELAY_SOURCE_URL")
    if not RELAY_TOKEN:
        missing.append("NOTIFICATION_RELAY_TOKEN")
    if not NAPCAT_GROUP_ID:
        missing.append("NAPCAT_GROUP_ID")
    if missing:
        names = ", ".join(missing)
        raise SystemExit(f"Missing required environment variables: {names}")


def fetch_notifications():
    url = f"{SOURCE_URL}/api/napcat-notifications?limit=10"
    data = request_json(url, headers=relay_headers())
    return data.get("notifications", [])


def process_notification(notification):
    notification_id = notification["id"]
    message = notification["message"]
    try:
        send_group_message(message)
    except Exception as exc:
        print(f"Notification {notification_id} failed: {exc}", file=sys.stderr)
        ack_notification(notification_id, "failed", str(exc))
        return

    ack_notification(notification_id, "sent")
    print(f"Notification {notification_id} sent.")


def send_group_message(message):
    endpoint = NAPCAT_API_URL
    if not endpoint.endswith("/send_group_msg"):
        endpoint = f"{endpoint}/send_group_msg"
    payload = {
        "group_id": int(NAPCAT_GROUP_ID) if NAPCAT_GROUP_ID.isdigit() else NAPCAT_GROUP_ID,
        "message": message,
    }
    headers = {"Content-Type": "application/json"}
    if NAPCAT_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {NAPCAT_ACCESS_TOKEN}"
    data = request_json(endpoint, payload=payload, headers=headers)
    retcode = data.get("retcode")
    if retcode not in (None, 0):
        raise RuntimeError(f"NapCat returned retcode={retcode}: {data}")


def ack_notification(notification_id, status, error=""):
    payload = {"status": status, "error": error}
    url = f"{SOURCE_URL}/api/napcat-notifications/{notification_id}/ack"
    request_json(url, payload=payload, headers=relay_headers())


def request_json(url, payload=None, headers=None):
    headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"non-JSON response from {url}: {body[:200]}") from exc


def relay_headers():
    return {"Authorization": f"Bearer {RELAY_TOKEN}"}


if __name__ == "__main__":
    main()
