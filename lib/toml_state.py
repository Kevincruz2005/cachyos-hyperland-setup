"""Preserve target-local Noctalia state; never import the author's private state."""
import copy
import datetime
import json
import math
import tomllib


def merge(base, additions):
    result = copy.deepcopy(base)
    for key, value in additions.items():
        if isinstance(value, dict) and isinstance(result.get(key, {}), dict):
            result[key] = merge(result.get(key, {}), value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def scalar(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value) if math.isfinite(value) else ("nan" if math.isnan(value) else "-inf" if value < 0 else "inf")
    if isinstance(value, list):
        return "[" + ", ".join(scalar(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(json.dumps(key) + " = " + scalar(item) for key, item in value.items()) + " }"
    raise ValueError("Unsupported target TOML value; manual merge required.")


def dump(data):
    lines = []

    def table(values, path):
        if path:
            lines.extend(["", "[" + ".".join(json.dumps(key) for key in path) + "]"])
        for key, value in values.items():
            if not isinstance(value, dict):
                lines.append(json.dumps(key) + " = " + scalar(value))
        for key, value in values.items():
            if isinstance(value, dict):
                table(value, path + [key])

    table(data, [])
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)
    return text.encode()


def merge_state(path, additions):
    original = tomllib.loads(path.read_text()) if path.exists() else {}
    return dump(merge(original, additions))
