<p align="center">
  <h1 align="center">💧 S I S T E M A &nbsp; H Í D R I C O &nbsp; C U M A N Á</h1>
  <p align="center"><strong>Plataforma de Monitoreo del Sistema de Agua Potable — Cumaná, Estado Sucre, Venezuela</strong></p>
  <p align="center">
    <em>Basado en <a href="https://github.com/BigBodyCobain/Shadowbroker">Shadowbroker</a> — Adaptado por Prof. César Rodríguez</em>
  </p>
</p>

---

## ¿Qué es?

**SistemaHidricoCumana** es una plataforma de monitoreo en tiempo real del sistema de distribución de agua potable de la ciudad de **Cumaná**, Venezuela. Permite visualizar en un mapa interactivo la infraestructura hídrica —desde el **Embalse Turimiquire** hasta la red de distribución urbana—, recibir datos de sensores IoT (reales o simulados), generar alertas automáticas y consultar datos climáticos de la zona.

El proyecto es un fork de [Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker), una plataforma de inteligencia de fuentes abiertas. Se reutiliza su infraestructura de mapas (MapLibre GL), backend (FastAPI) y sistema de capas de datos para crear una herramienta especializada en la gestión hídrica local.

### ¿Para quién es?

- **Operadores de acueductos** que necesitan un panel centralizado del estado del sistema
- **Investigadores y estudiantes** de ingeniería hidráulica, ambiental o civil
- **Comunidades organizadas** que quieran monitorear la disponibilidad de agua en su zona
- **Cualquier persona en Cumaná** interesada en entender cómo funciona el sistema de agua de su ciudad

---

## Componentes del Sistema Hídrico Monitoreado

| Componente | Descripción |
|---|---|
| **🏔️ Embalse Turimiquire** | Embalse principal del oriente venezolano (inaugurado 1988). Capacidad: ~130 millones m³ |
| **🕳️ Túnel de Trasvase Guamacán** | Conducto de ~12.5 km que transporta agua desde el embalse |
| **🏭 Planta Potabilizadora J.A. Anzoátegui** | Planta de tratamiento de agua. Capacidad: ~3000 L/s |
| **⚡ Estaciones de Bombeo** | 3 estaciones de re-bombeo (salida embalse, Cumaná norte, Cumaná sur) |
| **🗄️ Tanques de Almacenamiento** | Tanques elevados (Cerro El Peñón, San Luis) para regulación de presión |
| **🔵 Red de Distribución** | Red de tuberías urbanas que sirve ~180.000 habitantes |
| **🏞️ Río Manzanares** | Fuente secundaria que atraviesa Cumaná |
| **🔀 Derivaciones** | Ramales a Marigüitar y tubería submarina a la Península de Araya |

---

## ✨ Funcionalidades Principales

### 💧 Monitoreo en Tiempo Real
- **Panel de Sistema Hídrico** — Gauge del nivel del embalse, lecturas de sensores, alertas activas
- **Sensores IoT** — Recibe datos de nivel, presión, caudal, turbidez, pH y cloro residual
- **Alertas automáticas** — Semáforo de estado (🟢 operativo / 🟡 advertencia / 🔴 crítico) con umbrales configurables

### 🗺️ Mapa Interactivo
- **Infraestructura estática** — Polígono del embalse, líneas de tuberías/túnel, puntos de estaciones y tanques
- **Sensores dinámicos** — Puntos coloreados por estado que muestran valores en tiempo real
- **Capas toggleables** — Activa/desactiva cada componente del sistema desde el panel izquierdo
- **Múltiples estilos de mapa** — Default, Satélite, FLIR, NVG, CRT

### 🌧️ Datos Climáticos
- **Precipitación** — Datos de Open-Meteo para la zona del Turimiquire (gratis, sin API key)
- **Temperatura y humedad** — Condiciones actuales y pronóstico
- **Historial de 7 días** — Gráfico de barras de precipitación diaria

### 🛰️ Observación Satelital (heredado de Shadowbroker)
- **Sentinel-2** — Imágenes cada ~5 días a 10m de resolución del embalse
- **NASA MODIS** — Imágenes diarias del planeta
- **FIRMS** — Detección de incendios forestales cerca del embalse

### 📡 Simulación de Sensores
- **4 escenarios** — Normal, Sequía, Fuga en túnel, Contaminación
- **11 sensores** — Cubren todo el trayecto embalse → red de distribución
- **Fácil de reemplazar** — Diseñado para conectar sensores reales (ESP32, Arduino, etc.)

---

## ⚡ Inicio Rápido

### Opción 1: Docker (Recomendado)

```bash
git clone https://github.com/cero97-ctrl/SistemaHidricoCumana.git
cd SistemaHidricoCumana
docker compose pull
docker compose up -d
```

Abre `http://localhost:3000` en tu navegador.

### Opción 2: Desarrollo Local

#### Requisitos previos
- **Python 3.11+** y **pip**
- **Node.js 18+** y **npm**
- **Git**

#### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/cero97-ctrl/SistemaHidricoCumana.git
cd SistemaHidricoCumana

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install -r ../requirements.txt
cp .env.example .env            # Editar si es necesario

# 3. Frontend
cd ../frontend
npm install
```

#### Ejecución

Necesitas 3 terminales:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2: Frontend
cd frontend
npm run dev
```

```bash
# Terminal 3: Simulador de sensores
python scripts/simulador_turimiquire.py --escenario normal
```

Abre `http://localhost:3000` y activa la capa **"Sistema Hídrico Cumaná"** en el panel izquierdo.

---

## 📡 Uso del Simulador

El simulador genera datos realistas para todos los componentes del sistema hídrico:

```bash
# Operación normal — todos los valores en rango óptimo
python scripts/simulador_turimiquire.py

# Sequía — nivel del embalse bajando, caudal reducido
python scripts/simulador_turimiquire.py --escenario sequia

# Fuga en el túnel — caída de presión, reducción drástica de caudal
python scripts/simulador_turimiquire.py --escenario fuga

# Contaminación — turbidez alta, pH bajo, cloro insuficiente
python scripts/simulador_turimiquire.py --escenario contaminacion

# Configurar intervalo y número de ciclos
python scripts/simulador_turimiquire.py --escenario fuga --intervalo 5 --ciclos 20
```

### Sensores simulados

| Sensor | Componente | Medición | Unidad |
|---|---|---|---|
| `sensor_embalse_nivel` | Embalse | Nivel de agua | metros |
| `sensor_embalse_caudal` | Embalse | Caudal de salida | L/s |
| `sensor_tunel_presion` | Túnel | Presión | PSI |
| `sensor_tunel_caudal` | Túnel | Caudal | L/s |
| `sensor_planta_turbidez` | Planta | Turbidez | NTU |
| `sensor_planta_ph` | Planta | pH | pH |
| `sensor_planta_cloro` | Planta | Cloro residual | mg/L |
| `sensor_estacion1_presion` | Estación #1 | Presión | PSI |
| `sensor_estacion2_presion` | Estación #2 | Presión | PSI |
| `sensor_red_presion_norte` | Red Norte | Presión | PSI |
| `sensor_red_presion_sur` | Red Sur | Presión | PSI |

---

## 🚨 Sistema de Alertas

Las alertas se generan automáticamente cuando los valores cruzan umbrales predefinidos:

| Componente | Métrica | ⚠️ Advertencia | 🔴 Crítico |
|---|---|---|---|
| Embalse | Nivel bajo | < 255 m | < 245 m |
| Embalse | Nivel alto | > 278 m | > 280 m |
| Túnel | Presión | < 40 PSI | < 30 PSI |
| Túnel | Caudal | < 1000 L/s | < 500 L/s |
| Planta | Turbidez | > 4 NTU | > 8 NTU |
| Planta | pH bajo | < 6.5 | < 6.0 |
| Planta | pH alto | > 8.5 | > 9.0 |
| Planta | Cloro | < 0.5 mg/L | < 0.2 mg/L |
| Estación | Presión | < 35 PSI | < 25 PSI |
| Red | Presión | < 25 PSI | < 15 PSI |

---

## 🔌 API del Sistema Hídrico

El backend expone los siguientes endpoints para el módulo hídrico:

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/hidrico/telemetry` | Recibir lectura de un sensor |
| `GET` | `/api/hidrico/estado` | Estado consolidado del sistema |
| `GET` | `/api/hidrico/alertas` | Lista de alertas activas |
| `GET` | `/api/hidrico/infraestructura` | GeoJSON de infraestructura estática |
| `GET` | `/api/hidrico/sensores` | Últimas lecturas de todos los sensores |
| `GET` | `/api/hidrico/historial` | Historial de lecturas (últimas 200) |
| `GET` | `/api/hidrico/precipitacion` | Datos de precipitación (Open-Meteo) |

### Ejemplo: Enviar una lectura de sensor

```bash
curl -X POST http://localhost:8000/api/hidrico/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_embalse_nivel",
    "componente": "embalse",
    "tipo_medicion": "nivel",
    "valor": 265.5,
    "unidad": "metros",
    "lat": 10.133,
    "lng": -63.940
  }'
```

### Ejemplo: Consultar estado del sistema

```bash
curl http://localhost:8000/api/hidrico/estado
```

Respuesta:
```json
{
  "estado_general": "operativo",
  "total_sensores": 11,
  "total_alertas": 0,
  "alertas_criticas": 0,
  "alertas_advertencia": 0,
  "sensores_por_componente": {
    "embalse": 2,
    "tunel": 2,
    "planta": 3,
    "estacion_bombeo": 2,
    "red_distribucion": 2
  },
  "ultimo_reporte": 1746661200.0
}
```

---

## 🔧 Conectar Sensores Reales (ESP32 / Arduino)

El sistema está diseñado para reemplazar fácilmente los datos simulados con sensores IoT reales. Cualquier dispositivo que pueda hacer un `POST` HTTP puede enviar datos:

### Ejemplo con ESP32 (MicroPython)

```python
import urequests
import json

datos = {
    "sensor_id": "esp32_tanque_norte",
    "componente": "tanque",
    "tipo_medicion": "nivel",
    "valor": 3.2,
    "unidad": "metros",
    "lat": 10.460,
    "lng": -64.165
}

resp = urequests.post(
    "http://IP_DEL_SERVIDOR:8000/api/hidrico/telemetry",
    json=datos,
    headers={"Content-Type": "application/json"}
)
print(resp.json())
```

### Sensores recomendados

| Sensor | Medición | Precio aprox. |
|---|---|---|
| HC-SR04 / JSN-SR04T | Nivel de agua (ultrasónico) | $2-5 USD |
| YF-S201 | Caudal | $3-5 USD |
| Sensor de presión 0-1.2 MPa | Presión de tubería | $5-10 USD |
| Turbidímetro TSD-10 | Turbidez | $8-15 USD |
| Módulo pH PH-4502C | pH del agua | $5-10 USD |
| ESP32 DevKit | Microcontrolador WiFi | $3-8 USD |

---

## 🏗️ Arquitectura

```
SistemaHidricoCumana/
├── backend/                    # FastAPI (Python)
│   ├── main.py                 # Punto de entrada del servidor
│   ├── routers/
│   │   ├── hidrico.py          # ← API del sistema hídrico
│   │   ├── data.py             # API de datos generales
│   │   └── ...                 # Otros routers heredados
│   ├── data/
│   │   └── turimiquire_infrastructure.json  # ← GeoJSON de infraestructura
│   ├── services/
│   │   ├── data_fetcher.py     # Orquestador de fuentes de datos
│   │   └── fetchers/           # Fetchers individuales
│   └── scripts/
│       └── simulador_turimiquire.py  # Simulador simplificado
├── frontend/                   # Next.js + MapLibre GL
│   ├── src/
│   │   ├── app/page.tsx        # Dashboard principal
│   │   ├── components/
│   │   │   ├── HidricoPanel.tsx      # ← Panel de monitoreo hídrico
│   │   │   ├── MaplibreViewer.tsx    # Visor de mapa con capas
│   │   │   ├── WorldviewLeftPanel.tsx # Panel izquierdo de capas
│   │   │   └── map/
│   │   │       └── geoJSONBuilders.ts # Constructores de GeoJSON
│   │   └── hooks/
│   │       └── useDataPolling.ts     # Polling de datos en tiempo real
│   └── package.json
├── scripts/
│   └── simulador_turimiquire.py  # ← Simulador multi-escenario
├── requirements.txt
├── docker-compose.yml
└── README.md
```

### Stack Tecnológico

| Componente | Tecnología |
|---|---|
| **Backend** | Python 3.11+, FastAPI, Pydantic, uvicorn |
| **Frontend** | Next.js 14, React 18, MapLibre GL JS |
| **Mapa** | MapLibre GL con capas GeoJSON |
| **Datos climáticos** | Open-Meteo API (gratis, sin key) |
| **Imágenes satelitales** | Copernicus Sentinel-2, NASA MODIS |
| **Contenedores** | Docker, Docker Compose |

---

## 🔑 Variables de Entorno

### Backend (`backend/.env`)

```env
# Clave de administración (opcional, para proteger endpoints en producción)
ADMIN_KEY=tu_clave_secreta

# Puerto del backend
PORT=8000

# Otras claves opcionales heredadas de Shadowbroker
# SHODAN_API_KEY=...
# SENTINEL_CLIENT_ID=...
# SENTINEL_CLIENT_SECRET=...
```

---

## 🌐 Funcionalidades Heredadas de Shadowbroker

Al ser un fork de Shadowbroker, la plataforma mantiene todas sus capas OSINT originales:

- 🛩️ **Tráfico aéreo** — Vuelos comerciales, militares, jets privados (ADS-B)
- 🚢 **Tráfico marítimo** — 25.000+ buques AIS, actividad pesquera
- 🛰️ **Satélites** — Orbitas en tiempo real, estaciones SatNOGS/TinyGS
- 🌍 **Sismos y volcanes** — USGS, datos mundiales
- 🔥 **Incendios forestales** — NASA FIRMS
- 🌡️ **Calidad del aire** — Estaciones de monitoreo global
- 📷 **Cámaras CCTV** — 11.000+ cámaras en 6 países
- 📻 **Radio SDR** — KiwiSDR, escáneres de policía
- ⚡ **Infraestructura** — Plantas eléctricas, centros de datos, bases militares

Estas capas pueden activarse/desactivarse desde el panel izquierdo del dashboard.

---

## 📊 Fuentes de Datos del Módulo Hídrico

| Fuente | Datos | Costo |
|---|---|---|
| **Sensores IoT / Simulador** | Nivel, presión, caudal, calidad del agua | Gratuito |
| **Open-Meteo** | Precipitación, temperatura, humedad, pronóstico | Gratuito |
| **Sentinel-2** (Copernicus) | Imágenes satelitales del embalse cada ~5 días | Gratuito |
| **NASA MODIS/VIIRS** | Imágenes diarias, detección de incendios | Gratuito |
| **USGS Earthquakes** | Actividad sísmica cerca del embalse | Gratuito |
| **OpenStreetMap** | Base cartográfica de referencia | Gratuito |

> **Nota:** No existen APIs públicas de Hidrocaribe u otras autoridades hídricas venezolanas. Los datos de sensores son simulados o provistos por el operador. Si en el futuro se dispone de una API pública, se puede integrar fácilmente creando un nuevo fetcher en `backend/services/fetchers/`.

---

## 🗺️ Coordenadas de Referencia

| Lugar | Latitud | Longitud |
|---|---|---|
| Embalse Turimiquire (centro) | 10.133°N | 63.933°W |
| Planta Potabilizadora | 10.360°N | 64.100°W |
| Cumaná (centro) | 10.456°N | 64.167°W |
| Estación Bombeo #2 (Norte) | 10.470°N | 64.170°W |
| Estación Bombeo #3 (Sur) | 10.440°N | 64.175°W |

> Las coordenadas son aproximadas y se basan en datos públicos disponibles. Si tienes coordenadas más precisas de la infraestructura, puedes actualizarlas en `backend/data/turimiquire_infrastructure.json`.

---

## 🤝 Contribuir

1. Fork del repositorio
2. Crear una rama (`git checkout -b feature/mi-mejora`)
3. Commit (`git commit -m 'Agregar mi mejora'`)
4. Push (`git push origin feature/mi-mejora`)
5. Abrir un Pull Request

### Ideas para contribuir

- 📍 **Coordenadas más precisas** de la infraestructura hídrica
- 🔌 **Drivers para sensores** específicos (ESP32, Arduino, Raspberry Pi)
- 📊 **Visualizaciones** adicionales (gráficos históricos, predicciones)
- 🌐 **Datos de otras ciudades** venezolanas
- 📱 **App móvil** para reportes comunitarios de agua
- 🔗 **Integración con Hidrocaribe** si se dispone de datos

---

## ⚠️ Aviso Legal

Esta herramienta es un proyecto académico y experimental. No representa ninguna posición oficial de Hidrocaribe, HIDROCAPITAL, o cualquier otra autoridad hídrica venezolana. Los datos del sistema hídrico son simulados o provienen de fuentes públicas; no deben usarse para tomar decisiones operativas reales sin verificación independiente.

Las funcionalidades OSINT heredadas de Shadowbroker utilizan exclusivamente datos públicos y no introducen capacidades de vigilancia. El sistema no recopila ni transmite datos de los usuarios.

---

## 📜 Licencia

Este proyecto está bajo la **GNU Affero General Public License v3.0 (AGPL-3.0)**, heredada del proyecto original Shadowbroker.

---

## 🙏 Créditos

- **Adaptación y desarrollo:** Prof. César Rodríguez
- **Plataforma base:** [Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker) por BigBodyCobain
- **Datos climáticos:** [Open-Meteo](https://open-meteo.com/)
- **Mapa base:** [MapLibre GL JS](https://maplibre.org/) + [OpenStreetMap](https://www.openstreetmap.org/)
- **Imágenes satelitales:** [Copernicus Sentinel-2](https://sentinels.copernicus.eu/), [NASA MODIS](https://modis.gsfc.nasa.gov/)
