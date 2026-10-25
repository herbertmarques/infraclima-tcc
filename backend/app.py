from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Analysis, Dataset, Observation
from .processing import MAX_FILE_BYTES, demo_rows, parse_file, run_analysis
from .schemas import AnalysisRequest

@asynccontextmanager
async def lifespan(_app):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_demo(db)
    yield


app = FastAPI(
    title="InfraClima API",
    description="API local para análise exploratória de observações térmicas georreferenciadas em Manaus.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def dataset_dict(dataset: Dataset) -> dict:
    return {
        "id": dataset.id, "name": dataset.name, "description": dataset.description,
        "kind": dataset.kind, "source": dataset.source, "period": dataset.period,
        "license": dataset.license, "variableType": dataset.variable_type,
        "unit": dataset.unit,
        "resolution": dataset.resolution, "recordCount": dataset.record_count,
        "invalid": dataset.invalid_count, "duplicates": dataset.duplicate_count,
        "createdAt": dataset.created_at.isoformat() if dataset.created_at else None,
    }


def analysis_dict(analysis: Analysis) -> dict:
    return {
        "id": analysis.id, "datasetId": analysis.dataset_id,
        "algorithm": analysis.algorithm, "params": analysis.params,
        "status": analysis.status,
        "createdAt": analysis.created_at.isoformat() if analysis.created_at else None,
        "stats": analysis.result.get("stats", {}),
    }


def ensure_demo(db: Session, seed: int = 42) -> Dataset:
    name = f"Demonstração sintética — Manaus (semente {seed})"
    existing = db.scalar(select(Dataset).where(Dataset.kind == "demo", Dataset.name == name))
    if existing:
        return existing
    rows = demo_rows(seed)
    dataset = Dataset(
        name=name,
        description=f"Conjunto sintético determinístico para demonstração (semente {seed}). Não representa medições reais.",
        kind="demo", source="Dados sintéticos gerados pelo InfraClima",
        period="Não se aplica", license="Demonstração sem fonte externa",
        variable_type="sintético", resolution="sintética", record_count=len(rows),
    )
    dataset.observations = [Observation(
        external_id=row["id"], latitude=row["lat"], longitude=row["lon"],
        temperature=row["temp"], observed_at=row.get("observed_at", ""), quality={"synthetic": True},
    ) for row in rows]
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "service": "InfraClima API", "database": "ok"}


@app.get("/api/datasets")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.scalars(select(Dataset).order_by(desc(Dataset.created_at), desc(Dataset.id))).all()
    return {"items": [dataset_dict(item) for item in datasets]}


@app.get("/api/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(404, "Conjunto de dados não encontrado.")
    return dataset_dict(dataset)


@app.post("/api/datasets/demo")
def get_or_create_demo(seed: int = Query(42, ge=0, le=1000000), db: Session = Depends(get_db)):
    dataset = ensure_demo(db, seed)
    return dataset_dict(dataset)


@app.get("/api/datasets/{dataset_id}/observations")
def list_observations(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(404, "Conjunto de dados não encontrado.")
    rows = db.scalars(select(Observation).where(Observation.dataset_id == dataset_id).order_by(Observation.id)).all()
    return {"items": [{"id": row.external_id, "lat": row.latitude, "lon": row.longitude, "temp": row.temperature, "observed_at": row.observed_at, "quality": row.quality} for row in rows]}


@app.post("/api/datasets/import", status_code=201)
async def import_dataset(
    file: UploadFile = File(...),
    source: str = Form(""), period: str = Form(""), license: str = Form(""),
    variable_type: str = Form("other"), resolution: str = Form(""),
    unit: str = Form("°C"),
    latitude_field: str = Form(""), longitude_field: str = Form(""),
    temperature_field: str = Form(""), id_field: str = Form(""), observed_at_field: str = Form(""),
    db: Session = Depends(get_db),
):
    filename = file.filename or "dados.csv"
    if not filename.lower().endswith((".csv", ".json", ".geojson")):
        raise HTTPException(400, "Formato não suportado. Envie CSV ou GeoJSON.")
    if unit != "°C":
        raise HTTPException(422, "A unidade exigida nesta versão é °C. Converta os valores antes de importar e documente a transformação.")
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, "O arquivo excede o limite de 3 MB.")
    field_mapping = {"lat": latitude_field, "lon": longitude_field, "temp": temperature_field, "id": id_field, "observed_at": observed_at_field}
    try:
        rows, invalid, duplicates = parse_file(filename, content, field_mapping)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    dataset = Dataset(
        name=filename, description="Arquivo importado pelo usuário.", kind="import",
        source=source.strip() or "Não informada pelo usuário", period=period.strip() or "Não informado",
        license=license.strip() or "Não informada", variable_type=variable_type,
        resolution=resolution.strip() or "Não informada", record_count=len(rows),
        invalid_count=invalid, duplicate_count=duplicates,
    )
    dataset.observations = [Observation(
        external_id=row["id"], latitude=row["lat"], longitude=row["lon"],
        temperature=row["temp"], observed_at=row.get("observed_at", ""), quality={"synthetic": False},
    ) for row in rows]
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset_dict(dataset)


def get_dataset_rows(db: Session, dataset_id: int) -> tuple[Dataset, list[dict]]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(404, "Conjunto de dados não encontrado.")
    observations = db.scalars(select(Observation).where(Observation.dataset_id == dataset_id).order_by(Observation.id)).all()
    rows = [{"id": item.external_id, "lat": item.latitude, "lon": item.longitude, "temp": item.temperature, "observed_at": item.observed_at} for item in observations]
    return dataset, rows


@app.post("/api/analyses", status_code=201)
def create_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    dataset, rows = get_dataset_rows(db, request.dataset_id)
    try:
        result = run_analysis(rows, eps=request.eps, min_pts=request.min_pts, radius_km=request.radius_km, features=request.features)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    analysis = Analysis(
        dataset_id=dataset.id, params={"eps": request.eps, "minPts": request.min_pts, "radius": request.radius_km, "features": request.features},
        result=result,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {**analysis_dict(analysis), **result}


@app.get("/api/analyses/history")
def history(limit: int = 30, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 100)
    items = db.scalars(select(Analysis).order_by(desc(Analysis.created_at), desc(Analysis.id)).limit(limit)).all()
    total = db.scalar(select(func.count(Analysis.id))) or 0
    datasets = {item.id: item.name for item in db.scalars(select(Dataset)).all()}
    return {"total": total, "items": [{**analysis_dict(item), "datasetName": datasets.get(item.dataset_id, "Conjunto removido")} for item in items]}


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(404, "Análise não encontrada.")
    return {**analysis_dict(analysis), **analysis.result}


@app.get("/api/datasets/{dataset_id}/map")
def map_data(dataset_id: int, analysis_id: int | None = None, db: Session = Depends(get_db)):
    dataset, _ = get_dataset_rows(db, dataset_id)
    analysis = db.get(Analysis, analysis_id) if analysis_id else db.scalar(select(Analysis).where(Analysis.dataset_id == dataset_id).order_by(desc(Analysis.id)))
    if not analysis or analysis.dataset_id != dataset.id:
        raise HTTPException(404, "Execute uma análise deste conjunto para carregar o mapa.")
    return {"dataset": dataset_dict(dataset), "nodes": analysis.result["nodes"], "metadata": {"analysisId": analysis.id, "kind": dataset.kind}}


@app.get("/api/datasets/{dataset_id}/graph")
def graph_data(dataset_id: int, analysis_id: int | None = None, db: Session = Depends(get_db)):
    result = map_data(dataset_id, analysis_id, db)
    return {"nodes": result["nodes"], "edges": db.get(Analysis, result["metadata"]["analysisId"]).result["edges"], "metadata": result["metadata"]}


@app.get("/api/datasets/{dataset_id}/stats")
def dataset_stats(dataset_id: int, analysis_id: int | None = None, db: Session = Depends(get_db)):
    dataset, _ = get_dataset_rows(db, dataset_id)
    analysis = db.get(Analysis, analysis_id) if analysis_id else db.scalar(select(Analysis).where(Analysis.dataset_id == dataset_id).order_by(desc(Analysis.id)))
    if not analysis or analysis.dataset_id != dataset.id:
        raise HTTPException(404, "Execute uma análise deste conjunto para consultar as estatísticas.")
    return {"dataset": dataset_dict(dataset), "stats": analysis.result["stats"], "analysis": analysis_dict(analysis)}


@app.get("/api/analyses/{analysis_id}/export")
def export_analysis(analysis_id: int, format: str = "geojson", db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(404, "Análise não encontrada.")
    dataset = db.get(Dataset, analysis.dataset_id)
    result = analysis.result
    nodes, edges = result["nodes"], result["edges"]
    if format == "geojson":
        features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [node["lon"], node["lat"]]}, "properties": {key: value for key, value in node.items() if key not in ("lat", "lon", "features", "index")}} for node in nodes]
        for edge in edges:
            first, second = nodes[edge["source"]], nodes[edge["target"]]
            features.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[first["lon"], first["lat"]], [second["lon"], second["lat"]]]}, "properties": {"tipo": "aresta", "origem": first["id"], "destino": second["id"], "distancia_km": edge["km"]}})
        body = {"type": "FeatureCollection", "name": "InfraClima", "metadata": {"dataset": dataset_dict(dataset), "analysis": analysis_dict(analysis), "crs": "OGC:CRS84", "observacao": "Rótulos não são classes oficiais de risco térmico."}, "features": features}
        return Response(json.dumps(body, ensure_ascii=False), media_type="application/geo+json", headers={"Content-Disposition": "attachment; filename=infraclima_resultados.geojson"})
    if format not in {"nodes", "edges", "summary"}:
        raise HTTPException(400, "Formato de exportação inválido. Use geojson, nodes, edges ou summary.")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    def csv_safe(value):
        if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + value
        return value
    if format == "nodes":
        fields = ["id", "latitude", "longitude", "temperatura_c", "unidade", "data_hora", "cluster_id", "grau", "componente", "eps", "min_samples", "raio_grafo_km", "variaveis_dbscan", "fonte", "periodo", "licenca", "tipo_temperatura", "resolucao_escala", "registros_descartados", "registros_invalidos", "duplicatas_exatas"]
        writer.writerow(fields)
        values = analysis.params
        for node in nodes:
            writer.writerow([csv_safe(node["id"]), node["lat"], node["lon"], node["temp"], dataset.unit, csv_safe(node.get("observed_at", "")), node["cluster"], node["degree"], node["component"] + 1, values["eps"], values["minPts"], values["radius"], "|".join(values["features"]), csv_safe(dataset.source), csv_safe(dataset.period), csv_safe(dataset.license), csv_safe(dataset.variable_type), csv_safe(dataset.resolution), dataset.invalid_count + dataset.duplicate_count, dataset.invalid_count, dataset.duplicate_count])
        filename = "infraclima_nos.csv"
    elif format == "edges":
        fields = ["origem", "destino", "distancia_km", "cluster_origem", "cluster_destino", "raio_grafo_km"]
        writer.writerow(fields)
        for edge in edges:
            first, second = nodes[edge["source"]], nodes[edge["target"]]
            writer.writerow([csv_safe(first["id"]), csv_safe(second["id"]), edge["km"], first["cluster"], second["cluster"], analysis.params["radius"]])
        filename = "infraclima_arestas.csv"
    else:
        fields = ["tipo", "identificador", "observacoes", "media_temperatura_c", "minimo_c", "maximo_c", "desvio_padrao_c", "silhouette"]
        writer.writerow(fields)
        for profile in result["profiles"]: writer.writerow(["cluster", "Ruído" if profile["cluster"] < 0 else f"Grupo {profile['cluster']}", profile["count"], profile["mean"], profile["min"], profile["max"], profile["sd"], ""])
        stats = result["stats"]
        writer.writerow(["experimento", "total", stats["count"], stats["mean"], stats["min"], stats["max"], "", result["silhouette"] if result["silhouette"] is not None else ""])
        filename = "infraclima_resumo.csv"
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.get("/")
def root():
    return FileResponse(PROJECT_ROOT / "index.html")


app.mount("/src", StaticFiles(directory=PROJECT_ROOT / "src"), name="frontend-src")
