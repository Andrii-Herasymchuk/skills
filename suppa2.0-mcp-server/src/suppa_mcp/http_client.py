"""Shared HTTP client for the Suppa REST API."""

import json
import urllib.request
import urllib.error
from typing import Any

from suppa_mcp import config


def _headers(extra: dict | None = None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Accept": "application/json, text/plain, */*",
        "x-current-language": config.LANG,
        "x-timezone": config.TZ,
        "x-view-mode": "view",
    }
    if extra:
        h.update(extra)
    return h


def make_request(
    method: str,
    path: str,
    body: Any = None,
    *,
    timeout: int = 60,
    extra_headers: dict | None = None,
) -> Any:
    """Make an HTTP request to Suppa API. Returns parsed JSON or None."""
    if not config.API_KEY:
        raise RuntimeError("SUPPA_API_KEY environment variable is not set")

    url = f"{config.BASE_URL}{path}" if path.startswith("/") else path
    hdrs = _headers(extra_headers)

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json; charset=UTF-8"

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw or raw.strip() == "":
                return None
            result = json.loads(raw)
            # Unwrap common response wrappers
            if isinstance(result, dict):
                for key in ("data", "rows", "items", "result"):
                    if key in result and len(result) <= 3:
                        return result[key]
            return result
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}") from e


def make_request_raw_bytes(
    method: str,
    path: str,
    data: bytes,
    content_type: str,
    *,
    timeout: int = 120,
) -> Any:
    """Make a raw-bytes request (for multipart uploads)."""
    if not config.API_KEY:
        raise RuntimeError("SUPPA_API_KEY environment variable is not set")

    url = f"{config.BASE_URL}{path}" if path.startswith("/") else path
    hdrs = _headers({"Content-Type": content_type})

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {error_body}") from e


# ---------------------------------------------------------------------------
# High-level entity helpers
# ---------------------------------------------------------------------------

def data_url(entity: str, action: str) -> str:
    return f"/api/core/data/{entity}/{action}"


def custom_order_url(entity: str) -> str:
    return f"/api/core/data/custom-order/{entity}"


def search_entity(
    entity: str,
    filters: list | None = None,
    fields: dict | None = None,
    limit: int = 50,
    offset: int = 0,
    order_by: list | None = None,
    search_value: str = "",
) -> list:
    body = {
        "conditions": {"operator": "and", "filters": filters if filters is not None else []},
        "fields": fields or {"id": True},
        "limit": limit,
        "offset": offset,
        "orderBy": order_by if order_by is not None else [{"field": "createdAt", "order": "desc"}],
        "searchValue": search_value,
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    result = make_request("POST", data_url(entity, "search"), body)
    return result if isinstance(result, list) else []


def select_entity(
    entity: str,
    filters: list,
    fields: dict | None = None,
) -> dict | None:
    body = {
        "conditions": {"operator": "and", "filters": filters},
        "fields": fields or {"id": True},
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    result = make_request("POST", data_url(entity, "select") + "?markAsView=false", body)
    # The select endpoint returns a list of matching rows; return the first.
    if isinstance(result, list):
        return result[0] if result else None
    return result if isinstance(result, dict) else None


def insert_entity(entity: str, fields_list: list[dict], returning: dict | None = None) -> list:
    body: dict[str, Any] = {"fields": fields_list}
    if returning:
        body["returning"] = returning
    result = make_request("POST", data_url(entity, "insert"), body)
    return result if isinstance(result, list) else [result] if result else []


def update_entity(entity: str, instance_id: int, fields: dict) -> Any:
    body = {"fields": fields}
    return make_request("POST", data_url(entity, "update") + f"/{instance_id}", body)


def remove_entity(entity: str, filters: list) -> Any:
    body = {"conditions": {"operator": "and", "filters": filters}}
    return make_request("POST", data_url(entity, "remove"), body)
