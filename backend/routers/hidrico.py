"""Router for the Sistema Hídrico Cumaná monitoring layer.

Provides endpoints for:
- Receiving telemetry from water system sensors (IoT / simulated)
- Serving consolidated system status
- Serving static infrastructure GeoJSON
- Proxying precipitation data from Open-Meteo
- Managing alerts
"""

import json
import logging
import os
import time
import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from limiter import limiter
from auth import require_local_operator

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class SensorHidrico(BaseModel):
    """Telemetry reading from any water system sensor."""
    sensor_id: str
    componente: str = Field(
        ...,
        description="embalse | tunel | planta | estacion_bombeo | red_distribucion | rio | tanque",
    )
    tipo_medicion: str = Field(
        ...,
        description="nivel | presion | caudal | turbidez | ph | cloro_residual | temperatura",
    )
    valor: float
    unidad: str = Field(
        ...,
        description="metros | psi | lps | ntu | ph | mg_l | celsius",
    )
    lat: float | None = None
    lng: float | None = None


class AlertaHidrica(BaseModel):
    tipo: str  # critico | advertencia | info
    componente: str
    sensor_id: str
    mensaje: str
    timestamp: float


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_hidrico_lock = threading.Lock()

# Stores the latest reading per sensor_id
_sensor_latest: dict[str, dict[str, Any]] = {}

# Rolling history — last 200 readings across all sensors
_sensor_history: list[dict[str, Any]] = []
_MAX_HISTORY = 200

# Active alerts
_alertas_activas: list[dict[str, Any]] = []
_MAX_ALERTAS = 50

# Cached infrastructure GeoJSON (loaded once)
_infra_geojson: dict | None = None
_INFRA_PATH = Path(__file__).resolve().parents[1] / "data" / "turimiquire_infrastructure.json"

# Cached weather/precipitation data
_weather_cache: dict[str, Any] = {}
_weather_cache_ts: float = 0
_WEATHER_CACHE_TTL = 600  # 10 minutes


# ---------------------------------------------------------------------------
# Alert thresholds — configurable via env
# ---------------------------------------------------------------------------

UMBRALES = {
    "embalse": {
        "nivel": {"critico_bajo": 245.0, "advertencia_bajo": 255.0, "advertencia_alto": 278.0, "critico_alto": 280.0},
    },
    "tunel": {
        "presion": {"critico_bajo": 30.0, "advertencia_bajo": 40.0},
        "caudal": {"critico_bajo": 500.0, "advertencia_bajo": 1000.0},
    },
    "planta": {
        "turbidez": {"advertencia_alto": 4.0, "critico_alto": 8.0},
        "ph": {"critico_bajo": 6.0, "advertencia_bajo": 6.5, "advertencia_alto": 8.5, "critico_alto": 9.0},
        "cloro_residual": {"critico_bajo": 0.2, "advertencia_bajo": 0.5, "advertencia_alto": 2.0, "critico_alto": 4.0},
    },
    "estacion_bombeo": {
        "presion": {"critico_bajo": 25.0, "advertencia_bajo": 35.0},
    },
    "red_distribucion": {
        "presion": {"critico_bajo": 15.0, "advertencia_bajo": 25.0},
    },
}


def _evaluar_alertas(sensor: SensorHidrico) -> list[dict[str, Any]]:
    """Evaluate a sensor reading against thresholds and return any triggered alerts."""
    alertas: list[dict[str, Any]] = []
    comp_umbrales = UMBRALES.get(sensor.componente, {})
    tipo_umbrales = comp_umbrales.get(sensor.tipo_medicion, {})
    if not tipo_umbrales:
        return alertas

    v = sensor.valor
    now = time.time()

    # Check low thresholds
    if "critico_bajo" in tipo_umbrales and v < tipo_umbrales["critico_bajo"]:
        alertas.append({
            "tipo": "critico",
            "componente": sensor.componente,
            "sensor_id": sensor.sensor_id,
            "mensaje": f"CRÍTICO: {sensor.tipo_medicion} = {v} {sensor.unidad} (umbral: {tipo_umbrales['critico_bajo']})",
            "timestamp": now,
        })
    elif "advertencia_bajo" in tipo_umbrales and v < tipo_umbrales["advertencia_bajo"]:
        alertas.append({
            "tipo": "advertencia",
            "componente": sensor.componente,
            "sensor_id": sensor.sensor_id,
            "mensaje": f"Advertencia: {sensor.tipo_medicion} bajo = {v} {sensor.unidad} (umbral: {tipo_umbrales['advertencia_bajo']})",
            "timestamp": now,
        })

    # Check high thresholds
    if "critico_alto" in tipo_umbrales and v > tipo_umbrales["critico_alto"]:
        alertas.append({
            "tipo": "critico",
            "componente": sensor.componente,
            "sensor_id": sensor.sensor_id,
            "mensaje": f"CRÍTICO: {sensor.tipo_medicion} = {v} {sensor.unidad} (umbral máx: {tipo_umbrales['critico_alto']})",
            "timestamp": now,
        })
    elif "advertencia_alto" in tipo_umbrales and v > tipo_umbrales["advertencia_alto"]:
        alertas.append({
            "tipo": "advertencia",
            "componente": sensor.componente,
            "sensor_id": sensor.sensor_id,
            "mensaje": f"Advertencia: {sensor.tipo_medicion} alto = {v} {sensor.unidad} (umbral: {tipo_umbrales['advertencia_alto']})",
            "timestamp": now,
        })

    return alertas


def _load_infrastructure() -> dict:
    """Load the static infrastructure GeoJSON from disk (cached)."""
    global _infra_geojson
    if _infra_geojson is not None:
        return _infra_geojson
    try:
        with _INFRA_PATH.open("r", encoding="utf-8") as f:
            _infra_geojson = json.load(f)
        logger.info("Loaded water infrastructure GeoJSON: %d features", len(_infra_geojson.get("features", [])))
    except Exception as e:
        logger.error("Failed to load infrastructure GeoJSON: %s", e)
        _infra_geojson = {"type": "FeatureCollection", "features": []}
    return _infra_geojson


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/hidrico/telemetry")
@limiter.limit("120/minute")
async def hidrico_telemetry(request: Request, payload: SensorHidrico):
    """Receive a telemetry reading from any water system sensor.

    This endpoint is open for local IoT devices (ESP32, etc.) to POST to.
    For production deployments, add authentication via X-Admin-Key header.
    """
    data_point = payload.model_dump()
    data_point["timestamp"] = time.time()

    # Evaluate alerts
    nuevas_alertas = _evaluar_alertas(payload)
    data_point["alertas"] = nuevas_alertas

    with _hidrico_lock:
        # Update latest reading for this sensor
        _sensor_latest[payload.sensor_id] = data_point

        # Append to rolling history
        _sensor_history.append(data_point)
        if len(_sensor_history) > _MAX_HISTORY:
            _sensor_history.pop(0)

        # Store alerts
        for alerta in nuevas_alertas:
            _alertas_activas.append(alerta)
            if len(_alertas_activas) > _MAX_ALERTAS:
                _alertas_activas.pop(0)

    # Also push to the main data store so the slow-tier includes it
    try:
        from services.fetchers._store import latest_data, _data_lock, bump_data_version
        with _data_lock:
            if "turimiquire" not in latest_data:
                latest_data["turimiquire"] = []
            latest_data["turimiquire"] = list(_sensor_latest.values())

            # Expose consolidated status
            latest_data["hidrico_estado"] = _build_estado()
            latest_data["hidrico_alertas"] = list(_alertas_activas)
            bump_data_version()
    except Exception as e:
        logger.warning("Failed to update main data store: %s", e)

    return {
        "status": "ok",
        "sensor_id": payload.sensor_id,
        "alertas_nuevas": nuevas_alertas,
        "total_sensores_activos": len(_sensor_latest),
    }


@router.get("/api/hidrico/estado")
@limiter.limit("60/minute")
async def hidrico_estado(request: Request):
    """Get consolidated system status."""
    return JSONResponse(_build_estado())


@router.get("/api/hidrico/alertas")
@limiter.limit("60/minute")
async def hidrico_alertas(request: Request):
    """Get active alerts."""
    with _hidrico_lock:
        return JSONResponse({
            "alertas": list(_alertas_activas),
            "total": len(_alertas_activas),
        })


@router.get("/api/hidrico/infraestructura")
@limiter.limit("30/minute")
async def hidrico_infraestructura(request: Request):
    """Get static infrastructure GeoJSON."""
    infra = _load_infrastructure()
    return JSONResponse(infra)


@router.get("/api/hidrico/sensores")
@limiter.limit("60/minute")
async def hidrico_sensores(request: Request):
    """Get latest readings from all active sensors."""
    with _hidrico_lock:
        return JSONResponse({
            "sensores": list(_sensor_latest.values()),
            "total": len(_sensor_latest),
        })


@router.get("/api/hidrico/historial")
@limiter.limit("30/minute")
async def hidrico_historial(
    request: Request,
    sensor_id: str = Query(None, description="Filter by sensor ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get sensor reading history."""
    with _hidrico_lock:
        if sensor_id:
            history = [h for h in _sensor_history if h.get("sensor_id") == sensor_id]
        else:
            history = list(_sensor_history)
    return JSONResponse({
        "historial": history[-limit:],
        "total": len(history),
    })


@router.get("/api/hidrico/precipitacion")
@limiter.limit("20/minute")
async def hidrico_precipitacion(request: Request):
    """Get precipitation and weather data for the Turimiquire region via Open-Meteo.

    Data is cached for 10 minutes to avoid hitting the free API too aggressively.
    """
    global _weather_cache, _weather_cache_ts
    now = time.time()

    if _weather_cache and (now - _weather_cache_ts) < _WEATHER_CACHE_TTL:
        return JSONResponse(_weather_cache)

    try:
        import httpx
        # Turimiquire reservoir coordinates
        lat, lon = 10.133, -63.933
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m"
            f"&hourly=precipitation,rain,temperature_2m"
            f"&daily=precipitation_sum,rain_sum,temperature_2m_max,temperature_2m_min"
            f"&timezone=America/Caracas"
            f"&past_days=7&forecast_days=3"
        )
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        _weather_cache = {
            "source": "Open-Meteo",
            "location": {"lat": lat, "lon": lon, "name": "Embalse Turimiquire"},
            "current": data.get("current", {}),
            "hourly": data.get("hourly", {}),
            "daily": data.get("daily", {}),
            "fetched_at": now,
        }
        _weather_cache_ts = now
        logger.info("Fetched precipitation data from Open-Meteo for Turimiquire")
        return JSONResponse(_weather_cache)
    except Exception as e:
        logger.warning("Failed to fetch precipitation data: %s", e)
        if _weather_cache:
            return JSONResponse(_weather_cache)
        return JSONResponse({"error": str(e), "source": "Open-Meteo"}, status_code=502)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_estado() -> dict[str, Any]:
    """Build a consolidated system status snapshot."""
    with _hidrico_lock:
        sensores = dict(_sensor_latest)
        alertas = list(_alertas_activas)

    # Determine overall status
    tiene_critico = any(a["tipo"] == "critico" for a in alertas)
    tiene_advertencia = any(a["tipo"] == "advertencia" for a in alertas)

    if tiene_critico:
        estado_general = "critico"
    elif tiene_advertencia:
        estado_general = "advertencia"
    elif len(sensores) > 0:
        estado_general = "operativo"
    else:
        estado_general = "sin_datos"

    # Group sensors by component
    por_componente: dict[str, list] = {}
    for s in sensores.values():
        comp = s.get("componente", "otro")
        por_componente.setdefault(comp, []).append(s)

    return {
        "estado_general": estado_general,
        "total_sensores": len(sensores),
        "total_alertas": len(alertas),
        "alertas_criticas": sum(1 for a in alertas if a["tipo"] == "critico"),
        "alertas_advertencia": sum(1 for a in alertas if a["tipo"] == "advertencia"),
        "sensores_por_componente": {
            comp: len(items) for comp, items in por_componente.items()
        },
        "ultimo_reporte": max(
            (s.get("timestamp", 0) for s in sensores.values()), default=0
        ),
        "sensores": list(sensores.values()),
        "alertas": alertas[-10:],  # last 10 alerts
    }
