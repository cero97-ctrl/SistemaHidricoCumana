"""Simulador Multi-Componente del Sistema Hídrico de Cumaná.

Envía datos simulados a la API /api/hidrico/telemetry para todos los
componentes del sistema hídrico: embalse, túnel, planta, estaciones
de bombeo, red de distribución.

Uso:
  python scripts/simulador_turimiquire.py [--escenario normal|sequia|fuga|contaminacion]
"""

import time
import random
import argparse
import sys

try:
    import requests
except ImportError:
    print("❌ Falta la librería 'requests'. Instala con: pip install requests")
    sys.exit(1)

# --- Configuración ---
API_URL = "http://localhost:8000/api/hidrico/telemetry"
ADMIN_KEY = ""  # Dejar vacío para pruebas locales


# --- Definición de Sensores ---

SENSORES = {
    "embalse_nivel": {
        "sensor_id": "sensor_embalse_nivel",
        "componente": "embalse",
        "tipo_medicion": "nivel",
        "unidad": "metros",
        "lat": 10.133,
        "lng": -63.940,
        "normal": {"min": 258, "max": 272},
        "sequia": {"min": 240, "max": 250},
        "fuga": {"min": 255, "max": 265},
        "contaminacion": {"min": 260, "max": 270},
    },
    "embalse_caudal_salida": {
        "sensor_id": "sensor_embalse_caudal",
        "componente": "embalse",
        "tipo_medicion": "caudal",
        "unidad": "lps",
        "lat": 10.133,
        "lng": -63.933,
        "normal": {"min": 1800, "max": 2500},
        "sequia": {"min": 800, "max": 1200},
        "fuga": {"min": 1200, "max": 1800},
        "contaminacion": {"min": 1800, "max": 2300},
    },
    "tunel_presion": {
        "sensor_id": "sensor_tunel_presion",
        "componente": "tunel",
        "tipo_medicion": "presion",
        "unidad": "psi",
        "lat": 10.220,
        "lng": -64.025,
        "normal": {"min": 50, "max": 65},
        "sequia": {"min": 40, "max": 52},
        "fuga": {"min": 25, "max": 38},
        "contaminacion": {"min": 48, "max": 60},
    },
    "tunel_caudal": {
        "sensor_id": "sensor_tunel_caudal",
        "componente": "tunel",
        "tipo_medicion": "caudal",
        "unidad": "lps",
        "lat": 10.260,
        "lng": -64.055,
        "normal": {"min": 1600, "max": 2200},
        "sequia": {"min": 600, "max": 1000},
        "fuga": {"min": 400, "max": 800},
        "contaminacion": {"min": 1500, "max": 2000},
    },
    "planta_turbidez": {
        "sensor_id": "sensor_planta_turbidez",
        "componente": "planta",
        "tipo_medicion": "turbidez",
        "unidad": "ntu",
        "lat": 10.358,
        "lng": -64.098,
        "normal": {"min": 0.5, "max": 3.0},
        "sequia": {"min": 0.3, "max": 2.0},
        "fuga": {"min": 1.0, "max": 4.0},
        "contaminacion": {"min": 6.0, "max": 12.0},
    },
    "planta_ph": {
        "sensor_id": "sensor_planta_ph",
        "componente": "planta",
        "tipo_medicion": "ph",
        "unidad": "ph",
        "lat": 10.360,
        "lng": -64.100,
        "normal": {"min": 6.8, "max": 7.8},
        "sequia": {"min": 6.5, "max": 7.5},
        "fuga": {"min": 6.8, "max": 7.8},
        "contaminacion": {"min": 5.5, "max": 6.2},
    },
    "planta_cloro": {
        "sensor_id": "sensor_planta_cloro",
        "componente": "planta",
        "tipo_medicion": "cloro_residual",
        "unidad": "mg_l",
        "lat": 10.362,
        "lng": -64.102,
        "normal": {"min": 0.6, "max": 1.5},
        "sequia": {"min": 0.5, "max": 1.2},
        "fuga": {"min": 0.3, "max": 0.8},
        "contaminacion": {"min": 0.1, "max": 0.3},
    },
    "estacion1_presion": {
        "sensor_id": "sensor_estacion1_presion",
        "componente": "estacion_bombeo",
        "tipo_medicion": "presion",
        "unidad": "psi",
        "lat": 10.470,
        "lng": -64.170,
        "normal": {"min": 40, "max": 55},
        "sequia": {"min": 30, "max": 42},
        "fuga": {"min": 20, "max": 32},
        "contaminacion": {"min": 38, "max": 52},
    },
    "estacion2_presion": {
        "sensor_id": "sensor_estacion2_presion",
        "componente": "estacion_bombeo",
        "tipo_medicion": "presion",
        "unidad": "psi",
        "lat": 10.440,
        "lng": -64.175,
        "normal": {"min": 38, "max": 50},
        "sequia": {"min": 28, "max": 40},
        "fuga": {"min": 18, "max": 30},
        "contaminacion": {"min": 35, "max": 48},
    },
    "red_presion_norte": {
        "sensor_id": "sensor_red_presion_norte",
        "componente": "red_distribucion",
        "tipo_medicion": "presion",
        "unidad": "psi",
        "lat": 10.468,
        "lng": -64.170,
        "normal": {"min": 28, "max": 42},
        "sequia": {"min": 18, "max": 30},
        "fuga": {"min": 12, "max": 22},
        "contaminacion": {"min": 25, "max": 40},
    },
    "red_presion_sur": {
        "sensor_id": "sensor_red_presion_sur",
        "componente": "red_distribucion",
        "tipo_medicion": "presion",
        "unidad": "psi",
        "lat": 10.438,
        "lng": -64.175,
        "normal": {"min": 25, "max": 40},
        "sequia": {"min": 15, "max": 28},
        "fuga": {"min": 10, "max": 20},
        "contaminacion": {"min": 22, "max": 38},
    },
}

ESCENARIO_DESCRIPCIONES = {
    "normal": "✅ Operación normal — todos los valores en rango óptimo",
    "sequia": "🌵 Sequía — nivel del embalse bajando, caudal reducido",
    "fuga": "💧 Fuga en túnel — caída de presión, reducción drástica de caudal",
    "contaminacion": "☠️  Contaminación — turbidez alta, pH bajo, cloro insuficiente",
}


def generar_lectura(sensor: dict, escenario: str) -> dict:
    """Genera una lectura simulada para un sensor según el escenario."""
    rango = sensor.get(escenario, sensor["normal"])
    valor = round(random.uniform(rango["min"], rango["max"]), 2)

    return {
        "sensor_id": sensor["sensor_id"],
        "componente": sensor["componente"],
        "tipo_medicion": sensor["tipo_medicion"],
        "valor": valor,
        "unidad": sensor["unidad"],
        "lat": sensor.get("lat"),
        "lng": sensor.get("lng"),
    }


def enviar_lectura(datos: dict, headers: dict) -> dict | None:
    """Envía una lectura al API y retorna la respuesta."""
    try:
        resp = requests.post(API_URL, json=datos, headers=headers, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except requests.exceptions.ConnectionError:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Simulador del Sistema Hídrico de Cumaná"
    )
    parser.add_argument(
        "--escenario",
        choices=["normal", "sequia", "fuga", "contaminacion"],
        default="normal",
        help="Escenario de simulación (default: normal)",
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=10,
        help="Intervalo entre ciclos en segundos (default: 10)",
    )
    parser.add_argument(
        "--ciclos",
        type=int,
        default=0,
        help="Número de ciclos (0 = infinito, default: 0)",
    )
    args = parser.parse_args()

    headers = {"Content-Type": "application/json"}
    if ADMIN_KEY:
        headers["X-Admin-Key"] = ADMIN_KEY

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       📡 SIMULADOR — SISTEMA HÍDRICO DE CUMANÁ            ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Escenario: {ESCENARIO_DESCRIPCIONES[args.escenario]:<47}║")
    print(f"║  Destino:   {API_URL:<47}║")
    print(f"║  Sensores:  {len(SENSORES):<47}║")
    print(f"║  Intervalo: {args.intervalo}s{'':<44}║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    ciclo = 0
    while True:
        ciclo += 1
        if args.ciclos > 0 and ciclo > args.ciclos:
            break

        print(f"── Ciclo {ciclo} {'─' * 50}")
        alertas_totales = 0
        errores = 0

        for nombre, sensor in SENSORES.items():
            datos = generar_lectura(sensor, args.escenario)
            respuesta = enviar_lectura(datos, headers)

            if respuesta is None:
                errores += 1
                if errores == 1:
                    print("  ❌ Error de conexión — asegúrate de que el backend esté corriendo")
                continue

            nuevas_alertas = respuesta.get("alertas_nuevas", [])
            alertas_totales += len(nuevas_alertas)

            status = "✅" if not nuevas_alertas else ("🔴" if any(a["tipo"] == "critico" for a in nuevas_alertas) else "🟡")
            print(
                f"  {status} {sensor['componente'].upper():>18} | "
                f"{sensor['tipo_medicion']:>15} = {datos['valor']:>8.2f} {datos['unidad']:>6}"
                f"{'  ⚠️  ' + nuevas_alertas[0]['mensaje'][:40] if nuevas_alertas else ''}"
            )

        if errores == len(SENSORES):
            print("\n  ❌ Todos los envíos fallaron. ¿Está el backend corriendo en el puerto 8000?")
            print("     Reintentando en 10 segundos...\n")
            time.sleep(10)
            continue

        print(f"  ── {len(SENSORES) - errores}/{len(SENSORES)} sensores reportados | {alertas_totales} alertas nuevas")
        print()

        time.sleep(args.intervalo)

    print("🏁 Simulación finalizada.")


if __name__ == "__main__":
    main()
