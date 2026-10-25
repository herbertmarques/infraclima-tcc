"""Validação e processamento determinístico dos dados do InfraClima."""
from __future__ import annotations

import csv
import io
import math
import re
from collections import deque
from datetime import date, datetime
from statistics import mean, pstdev
from typing import Any

MAX_RECORDS = 800
MAX_FILE_BYTES = 3 * 1024 * 1024
EARTH_RADIUS_KM = 6371.0


def demo_rows(seed: int = 42) -> list[dict[str, Any]]:
    rows = []
    groups = [(-3.119, -60.022, 34.8), (-3.088, -60.015, 39.2), (-3.145, -59.998, 31.4)]
    number = 1
    offset = seed - 42
    for group, (base_lat, base_lon, base_temp) in enumerate(groups):
        for i in range(16):
            a, b = i % 4, i // 4
            jitter = ((i * 7 + group * 3 + offset) % 9 - 4) * 0.00125
            rows.append({
                "id": f"SIM-{number:03d}",
                "lat": base_lat + (a - 1.5) * 0.002 + jitter * 0.25,
                "lon": base_lon + (b - 1.5) * 0.002 - jitter * 0.35,
                "temp": round(base_temp + ((i * 13 + group * 7 + offset) % 11 - 5) * 0.42, 2),
                "observed_at": "",
            })
            number += 1
    return rows


def _header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\u0300-\u036f]", "", __import__("unicodedata").normalize("NFD", text))
    return re.sub(r"[^a-z0-9_]", "", text)


def _parse_csv(text: str) -> list[dict]:
    first = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if first.count(";") > first.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("CSV vazio ou sem cabeçalho.")
    rows = []
    for row in reader:
        rows.append({_header(key): value for key, value in row.items() if key is not None})
        if len(rows) > MAX_RECORDS * 2:
            raise ValueError(f"O arquivo excede o limite de {MAX_RECORDS} registros de entrada.")
    return rows


def _parse_geojson(text: str) -> list[dict]:
    import json
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("O arquivo JSON/GeoJSON não tem sintaxe válida.") from exc
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("GeoJSON precisa ser uma FeatureCollection.")
    rows = []
    for i, feature in enumerate(data["features"]):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            continue
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        row = {_header(k): v for k, v in (feature.get("properties") or {}).items()}
        row.update({"longitude": coordinates[0], "latitude": coordinates[1]})
        row.setdefault("id", f"OBS-{i + 1}")
        rows.append(row)
    return rows


def parse_file(filename: str, content: bytes, field_mapping: dict[str, str] | None = None) -> tuple[list[dict], int, int]:
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("O arquivo excede o limite de 3 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("O arquivo deve estar codificado em UTF-8.") from exc
    rows = _parse_csv(text) if filename.lower().endswith(".csv") else _parse_geojson(text)
    return normalize_rows(rows, field_mapping)


def normalize_rows(rows: list[dict], field_mapping: dict[str, str] | None = None) -> tuple[list[dict], int, int]:
    aliases = {
        "lat": ("latitude", "lat", "y"),
        "lon": ("longitude", "lon", "lng", "long", "x"),
        "temp": ("temperatura", "temperatura_c", "temperature", "temperature_c", "temp", "lst_c", "lst", "temperaturadesuperficie"),
        "id": ("id", "codigo", "code"),
        "observed_at": ("observed_at", "datetime", "timestamp", "data", "data_hora", "date", "time"),
    }
    out, seen, invalid, duplicates = [], set(), 0, 0
    field_mapping = {key: _header(value) for key, value in (field_mapping or {}).items() if value}
    for index, original in enumerate(rows, 1):
        row = {_header(k): v for k, v in original.items()}
        values = {}
        for key, names in aliases.items():
            selected = field_mapping.get(key)
            candidates = ([selected] if selected else []) + list(names)
            values[key] = next((row.get(name) for name in candidates if row.get(name) not in (None, "")), None)
        def numeric(value):
            if isinstance(value, str):
                value = value.strip().replace(",", ".")
            return float(value)
        try:
            lat, lon, temp = numeric(values["lat"]), numeric(values["lon"]), numeric(values["temp"])
            if not all(math.isfinite(x) for x in (lat, lon, temp)) or abs(lat) > 90 or abs(lon) > 180 or not -100 <= temp <= 100:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            invalid += 1
            continue
        observed_at = str(values["observed_at"] or "").strip()
        if observed_at:
            parsed_date = observed_at.replace("Z", "+00:00")
            valid_date = False
            try:
                datetime.fromisoformat(parsed_date)
                valid_date = True
            except ValueError:
                try:
                    date.fromisoformat(parsed_date)
                    valid_date = True
                except ValueError:
                    for date_format in ("%d/%m/%Y", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"):
                        try:
                            datetime.strptime(observed_at, date_format)
                            valid_date = True
                            break
                        except ValueError:
                            pass
            if not valid_date:
                invalid += 1
                continue
        identity = (round(lat, 7), round(lon, 7), round(temp, 4))
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        out.append({"id": str(values["id"] or f"OBS-{index:04d}"), "lat": lat, "lon": lon, "temp": temp, "observed_at": observed_at})
        if len(out) > MAX_RECORDS:
            raise ValueError(f"O limite é {MAX_RECORDS} pontos válidos.")
    if len(out) < 3:
        raise ValueError(f"Foram encontrados apenas {len(out)} pontos válidos; são necessários ao menos 3.")
    return out, invalid, duplicates


def _standardize(values: list[float]) -> list[float]:
    center = mean(values)
    sd = pstdev(values) or 1.0
    return [(value - center) / sd for value in values]


def _dbscan(rows: list[dict], eps: float, min_pts: int, features: list[str]) -> list[int]:
    names = {"lat": "lat", "lon": "lon", "temp": "temp"}
    vectors = list(zip(*[_standardize([row[names[name]] for row in rows]) for name in features]))
    labels: list[int | None] = [None] * len(rows)
    def neighbors(index):
        return [other for other, vector in enumerate(vectors)
                if math.sqrt(sum((a - b) ** 2 for a, b in zip(vectors[index], vector))) <= eps]
    cluster = 0
    for index in range(len(rows)):
        if labels[index] is not None:
            continue
        nearby = neighbors(index)
        if len(nearby) < min_pts:
            labels[index] = -1
            continue
        labels[index] = cluster
        queue = deque(item for item in nearby if item != index)
        queued = set(queue)
        while queue:
            current = queue.popleft()
            if labels[current] == -1:
                labels[current] = cluster
            if labels[current] is not None:
                continue
            labels[current] = cluster
            more = neighbors(current)
            if len(more) >= min_pts:
                for item in more:
                    if item not in queued:
                        queued.add(item)
                        queue.append(item)
        cluster += 1
    return [int(label) for label in labels]


def haversine_km(a: dict, b: dict) -> float:
    rad = math.pi / 180
    lat1, lat2 = a["lat"] * rad, b["lat"] * rad
    dlat, dlon = (b["lat"] - a["lat"]) * rad, (b["lon"] - a["lon"]) * rad
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1, value)))


def _silhouette(rows: list[dict], labels: list[int], features: list[str]):
    indexes = [i for i, label in enumerate(labels) if label >= 0]
    groups = sorted({labels[i] for i in indexes})
    if len(groups) < 2 or len(indexes) <= len(groups) or len(indexes) > 220:
        return None
    vectors = list(zip(*[_standardize([row[key] for row in rows]) for key in features]))
    scores = []
    for index in indexes:
        within, between = [], {group: [] for group in groups if group != labels[index]}
        for other in indexes:
            if other == index: continue
            distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(vectors[index], vectors[other])))
            if labels[other] == labels[index]: within.append(distance)
            else: between[labels[other]].append(distance)
        if not within: continue
        a = mean(within)
        b = min(mean(values) for values in between.values() if values)
        scores.append((b - a) / max(a, b, 1e-12))
    return round(mean(scores), 3) if scores else None


def run_analysis(raw: list[dict], *, eps: float, min_pts: int, radius_km: float, features: list[str]) -> dict:
    allowed = {"lat", "lon", "temp"}
    if not math.isfinite(eps) or eps <= 0 or not math.isfinite(radius_km) or radius_km <= 0 or min_pts < 2:
        raise ValueError("Parâmetros inválidos. ε e raio devem ser positivos; mínimo de pontos deve ser inteiro ≥ 2.")
    if not features or len(set(features)) != len(features) or any(f not in allowed for f in features):
        raise ValueError("Selecione uma ou mais variáveis válidas para o DBSCAN.")
    if len(raw) < min_pts:
        raise ValueError(f"Há {len(raw)} pontos; o mínimo configurado é {min_pts}.")
    labels = _dbscan(raw, eps, min_pts, features)
    nodes = [{**row, "cluster": labels[index], "degree": 0, "component": -1, "index": index} for index, row in enumerate(raw)]
    edges = []
    adjacency = [[] for _ in nodes]
    for i, node in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            distance = haversine_km(node, nodes[j])
            if distance <= radius_km:
                edges.append({"source": i, "target": j, "km": distance})
                nodes[i]["degree"] += 1
                nodes[j]["degree"] += 1
                adjacency[i].append(j); adjacency[j].append(i)
    component_count = 0
    for i, node in enumerate(nodes):
        if node["component"] >= 0: continue
        node["component"] = component_count
        queue = deque([i])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if nodes[neighbor]["component"] < 0:
                    nodes[neighbor]["component"] = component_count
                    queue.append(neighbor)
        component_count += 1
    profiles = []
    for cluster in sorted(set(labels)):
        values = [nodes[i]["temp"] for i, label in enumerate(labels) if label == cluster]
        profiles.append({"cluster": cluster, "count": len(values), "mean": mean(values), "min": min(values), "max": max(values), "sd": pstdev(values) if len(values) > 1 else 0.0})
    counts = {}
    for edge in edges:
        a, b = nodes[edge["source"]]["cluster"], nodes[edge["target"]]["cluster"]
        counts[(a, b)] = counts.get((a, b), 0) + 1
    adjacency_summary = [{"a": a, "b": b, "count": count} for (a, b), count in sorted(counts.items(), key=lambda item: -item[1])]
    temps = [node["temp"] for node in nodes]
    return {
        "nodes": nodes, "edges": edges, "components": component_count,
        "profiles": profiles, "adjacency": adjacency_summary,
        "silhouette": _silhouette(raw, labels, features),
        "params": {"eps": eps, "minPts": min_pts, "radius": radius_km, "features": features},
        "stats": {"count": len(nodes), "mean": mean(temps), "min": min(temps), "max": max(temps), "clusters": len({x for x in labels if x >= 0}), "noise": labels.count(-1), "edges": len(edges), "components": component_count},
    }
