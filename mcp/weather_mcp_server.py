#!/usr/bin/env python3
# Minimal MCP (Model Context Protocol) server over stdio (newline-delimited JSON-RPC).
#
# Implements:
# - initialize
# - tools/list
# - tools/call  (tool: get_weather)
# - ping
# - resources/list, resources/read, prompts/list, prompts/get (empty stubs)
#
# Weather data is fetched from Open-Meteo (no API key required).

import json
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


SERVER_NAME = "weather-mcp"
SERVER_VERSION = "0.1.0"


def _send(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error(_id: Optional[int], code: int, message: str, data: Any = None) -> None:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    _send({"jsonrpc": "2.0", "id": _id, "error": err})


def _ok(_id: Optional[int], result: Any) -> None:
    _send({"jsonrpc": "2.0", "id": _id, "result": result})


def _http_get_json(url: str, timeout_sec: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def _geocode_city(city: str) -> Tuple[float, float, str]:
    q = urllib.parse.urlencode(
        {"name": city, "count": 1, "language": "zh", "format": "json"},
        encoding="utf-8",
        safe="",
    )
    url = f"https://geocoding-api.open-meteo.com/v1/search?{q}"
    data = _http_get_json(url)
    results = data.get("results") or []
    if not results:
        raise ValueError(f"未找到城市: {city}")
    r0 = results[0]
    lat = float(r0["latitude"])
    lon = float(r0["longitude"])
    # e.g. "Beijing, Beijing, China"
    display = r0.get("name") or city
    admin1 = r0.get("admin1")
    country = r0.get("country")
    parts = [p for p in [display, admin1, country] if p]
    return lat, lon, ", ".join(parts)


def _get_weather(lat: float, lon: float) -> Dict[str, Any]:
    q = urllib.parse.urlencode(
        {
            "latitude": f"{lat:.6f}",
            "longitude": f"{lon:.6f}",
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
        encoding="utf-8",
        safe=",",
    )
    url = f"https://api.open-meteo.com/v1/forecast?{q}"
    return _http_get_json(url)


def _tool_spec_get_weather() -> Dict[str, Any]:
    return {
        "name": "get_weather",
        "description": "获取指定城市(或经纬度)的当前天气信息（数据源：Open-Meteo，无需 API Key）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，例如：北京/Shanghai/Tokyo"},
                "latitude": {"type": "number", "description": "纬度（与 longitude 一起使用）"},
                "longitude": {"type": "number", "description": "经度（与 latitude 一起使用）"},
            },
            "additionalProperties": False,
        },
    }


def _handle_tools_call(_id: Optional[int], params: Dict[str, Any]) -> None:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        _error(_id, -32602, "Invalid params: 'arguments' must be an object")
        return

    if name != "get_weather":
        _error(_id, -32601, f"Unknown tool: {name}")
        return

    city = arguments.get("city")
    lat = arguments.get("latitude")
    lon = arguments.get("longitude")

    try:
        place = None
        if city:
            lat_f, lon_f, place = _geocode_city(str(city))
        elif lat is not None and lon is not None:
            lat_f, lon_f = float(lat), float(lon)
            place = f"{lat_f:.6f},{lon_f:.6f}"
        else:
            raise ValueError("请提供 city 或 (latitude + longitude)")

        raw = _get_weather(lat_f, lon_f)
        current = raw.get("current") or {}
        unit = (raw.get("current_units") or {}).get("temperature_2m") or "°C"
        wind_unit = (raw.get("current_units") or {}).get("wind_speed_10m") or "km/h"

        text = (
            f"{place} 当前天气：\n"
            f"- 温度: {current.get('temperature_2m')} {unit}\n"
            f"- 体感: {current.get('apparent_temperature')} {unit}\n"
            f"- 风速: {current.get('wind_speed_10m')} {wind_unit}\n"
            f"- 天气码(weather_code): {current.get('weather_code')}\n"
            f"- 时间: {current.get('time')}\n"
        )

        _ok(
            _id,
            {
                "content": [{"type": "text", "text": text}],
                "structuredContent": {
                    "place": place,
                    "latitude": lat_f,
                    "longitude": lon_f,
                    "current": current,
                    "raw": raw,
                },
                "isError": False,
            },
        )
    except Exception as e:
        _ok(
            _id,
            {
                "content": [{"type": "text", "text": f"获取天气失败: {e}"}],
                "structuredContent": {"error": str(e)},
                "isError": True,
            },
        )


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            # Ignore non-JSON
            continue

        method = msg.get("method")
        _id = msg.get("id")
        params = msg.get("params") or {}

        # Notifications: no id
        if _id is None and isinstance(method, str) and method.startswith("notifications/"):
            continue

        if method == "initialize":
            protocol_version = None
            if isinstance(params, dict):
                protocol_version = params.get("protocolVersion")
            protocol_version = protocol_version or "2024-11-05"
            _ok(
                _id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        elif method == "tools/list":
            _ok(_id, {"tools": [_tool_spec_get_weather()], "nextCursor": None})
        elif method == "tools/call":
            if not isinstance(params, dict):
                _error(_id, -32602, "Invalid params")
            else:
                _handle_tools_call(_id, params)
        elif method == "ping":
            _ok(_id, {})
        elif method == "resources/list":
            _ok(_id, {"resources": [], "nextCursor": None})
        elif method == "resources/templates/list":
            _ok(_id, {"resourceTemplates": [], "nextCursor": None})
        elif method == "resources/read":
            # Not implemented
            _ok(_id, {"contents": []})
        elif method == "prompts/list":
            _ok(_id, {"prompts": [], "nextCursor": None})
        elif method == "prompts/get":
            _ok(_id, {"messages": []})
        else:
            _error(_id, -32601, f"Method not found: {method}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

