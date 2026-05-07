"""Simulador simplificado del Sistema Hídrico (backend/scripts).

Este archivo es la versión simplificada. Para la versión completa con
escenarios configurables, usa scripts/simulador_turimiquire.py en la
raíz del proyecto.
"""

import time
import random
import sys

try:
    import requests
except ImportError:
    print("❌ Falta 'requests'. Instala con: pip install requests")
    sys.exit(1)

API_URL = "http://localhost:8000/api/hidrico/telemetry"
ADMIN_KEY = ""

SENSORES = [
    {"sensor_id": "sensor_embalse_nivel", "componente": "embalse", "tipo_medicion": "nivel", "unidad": "metros", "lat": 10.133, "lng": -63.940, "min": 248, "max": 272},
    {"sensor_id": "sensor_tunel_presion", "componente": "tunel", "tipo_medicion": "presion", "unidad": "psi", "lat": 10.220, "lng": -64.025, "min": 38, "max": 62},
    {"sensor_id": "sensor_tunel_caudal", "componente": "tunel", "tipo_medicion": "caudal", "unidad": "lps", "lat": 10.260, "lng": -64.055, "min": 1200, "max": 2200},
    {"sensor_id": "sensor_planta_turbidez", "componente": "planta", "tipo_medicion": "turbidez", "unidad": "ntu", "lat": 10.358, "lng": -64.098, "min": 0.5, "max": 5.0},
    {"sensor_id": "sensor_planta_ph", "componente": "planta", "tipo_medicion": "ph", "unidad": "ph", "lat": 10.360, "lng": -64.100, "min": 6.5, "max": 8.0},
    {"sensor_id": "sensor_estacion1_presion", "componente": "estacion_bombeo", "tipo_medicion": "presion", "unidad": "psi", "lat": 10.470, "lng": -64.170, "min": 30, "max": 52},
    {"sensor_id": "sensor_red_presion_norte", "componente": "red_distribucion", "tipo_medicion": "presion", "unidad": "psi", "lat": 10.468, "lng": -64.170, "min": 18, "max": 40},
]

def simular():
    headers = {"Content-Type": "application/json"}
    if ADMIN_KEY:
        headers["X-Admin-Key"] = ADMIN_KEY

    print(f"📡 Simulador rápido — {len(SENSORES)} sensores → {API_URL}")

    while True:
        for s in SENSORES:
            datos = {
                "sensor_id": s["sensor_id"],
                "componente": s["componente"],
                "tipo_medicion": s["tipo_medicion"],
                "valor": round(random.uniform(s["min"], s["max"]), 2),
                "unidad": s["unidad"],
                "lat": s["lat"],
                "lng": s["lng"],
            }
            try:
                resp = requests.post(API_URL, json=datos, headers=headers, timeout=5)
                if resp.status_code == 200:
                    r = resp.json()
                    alertas = r.get("alertas_nuevas", [])
                    status = "⚠️" if alertas else "✅"
                    print(f"  {status} {s['componente']:>18} | {s['tipo_medicion']:>10} = {datos['valor']:>8.2f} {s['unidad']}")
                else:
                    print(f"  ❌ HTTP {resp.status_code}")
            except Exception:
                print("  ❌ Sin conexión al backend")
                break
        print()
        time.sleep(10)

if __name__ == "__main__":
    simular()