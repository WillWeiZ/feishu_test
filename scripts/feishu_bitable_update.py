#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
import urllib.parse


FEISHU_BASE = "https://open.feishu.cn"


def http_request(method: str, url: str, headers: dict = None, data: dict | None = None):
    req_headers = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        req_headers.update(headers)

    if data is not None:
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    req = urllib.request.Request(url=url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset)
            if text:
                return json.loads(text)
            return {}
    except urllib.error.HTTPError as e:
        try:
            err_text = e.read().decode("utf-8")
        except Exception:
            err_text = str(e)
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {err_text}")


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = f"{FEISHU_BASE}/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}
    data = http_request("POST", url, data=payload)
    if data.get("code") not in (0, None):
        raise RuntimeError(f"Failed to get tenant_access_token: {data}")
    token = data.get("tenant_access_token") or data.get("tenant_access_token", "")
    if not token:
        # Some responses use access_token; but Feishu should use tenant_access_token
        token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"No tenant_access_token in response: {data}")
    return token


def list_records(app_token: str, table_id: str, tenant_token: str, page_size: int = 500):
    records = []
    page_token = None

    while True:
        query = {
            "page_size": str(page_size),
            # Use field_id so we can update with field IDs like fldXXXX
            "field_id_type": "field_id",
        }
        if page_token:
            query["page_token"] = page_token
        qstr = urllib.parse.urlencode(query)
        url = f"{FEISHU_BASE}/open-apis/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables/{urllib.parse.quote(table_id)}/records?{qstr}"
        data = http_request(
            "GET",
            url,
            headers={"Authorization": f"Bearer {tenant_token}"},
        )

        if data.get("code") not in (0, None):
            raise RuntimeError(f"Failed to list records: {data}")

        items = data.get("data", {}).get("items", [])
        records.extend(items)

        has_more = data.get("data", {}).get("has_more")
        page_token = data.get("data", {}).get("page_token")
        if not has_more:
            break
        # Gentle pause to avoid rate limits
        time.sleep(0.2)

    return records


def update_record_field(app_token: str, table_id: str, record_id: str, field_id: str, value, tenant_token: str):
    url = f"{FEISHU_BASE}/open-apis/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables/{urllib.parse.quote(table_id)}/records/{urllib.parse.quote(record_id)}"
    payload = {
        # Ensure the server interprets keys as field IDs
        "fields": {field_id: value},
    }
    data = http_request(
        "PATCH",
        url,
        headers={
            "Authorization": f"Bearer {tenant_token}",
            # Some endpoints also accept X-Field-Id-Type header, but using body keys + query is enough
        },
        data=payload,
    )
    if data.get("code") not in (0, None):
        raise RuntimeError(f"Failed to update record {record_id}: {data}")
    return data.get("data", {})


def main():
    # Prefer environment variables; optional .env support (very simple parser)
    env_path = os.environ.get("ENV_FILE", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)

    app_id = os.environ.get("APP_ID")
    app_secret = os.environ.get("APP_SECRET")
    app_token = os.environ.get("APP_TOKEN")  # Bitable app token
    table_id = os.environ.get("TABLE_ID")
    target_field_id = os.environ.get("TARGET_FIELD_ID")

    missing = [k for k in ["APP_ID", "APP_SECRET", "APP_TOKEN", "TABLE_ID", "TARGET_FIELD_ID"] if not os.environ.get(k)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        print("Set them in your environment or .env file.", file=sys.stderr)
        sys.exit(2)

    print("Getting tenant access token ...")
    token = get_tenant_access_token(app_id, app_secret)
    print("OK")

    print("Listing records ...")
    records = list_records(app_token, table_id, token)
    print(f"Found {len(records)} records")

    # Show a preview of the first 5 records
    for i, rec in enumerate(records[:5]):
        rid = rec.get("record_id")
        fields = rec.get("fields", {})
        print(f"Record {i+1}: id={rid}, fields_keys={list(fields.keys())}")

    # Write dummy data to the specified column for all records
    print(f"Updating field {target_field_id} with dummy values ...")
    updated = 0
    failed = 0
    for idx, rec in enumerate(records, start=1):
        rid = rec.get("record_id")
        if not rid:
            failed += 1
            continue
        dummy_value = f"Dummy {idx}"
        try:
            update_record_field(app_token, table_id, rid, target_field_id, dummy_value, token)
            updated += 1
            if updated % 20 == 0:
                print(f"Updated {updated} records...")
        except Exception as e:
            failed += 1
            print(f"Failed to update record {rid}: {e}")
            # Continue updating others
            continue

    print(f"Done. Updated={updated}, Failed={failed}")


if __name__ == "__main__":
    main()

