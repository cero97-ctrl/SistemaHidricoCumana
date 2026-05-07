'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Droplets,
  AlertTriangle,
  Activity,
  Thermometer,
  CloudRain,
  Gauge,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Waves,
  Zap,
  Minus,
  Plus,
} from 'lucide-react';
import { API_BASE } from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SensorReading {
  sensor_id: string;
  componente: string;
  tipo_medicion: string;
  valor: number;
  unidad: string;
  timestamp: number;
  lat?: number;
  lng?: number;
  alertas?: Array<{ tipo: string; mensaje: string }>;
}

interface AlertaHidrica {
  tipo: string;
  componente: string;
  sensor_id: string;
  mensaje: string;
  timestamp: number;
}

interface EstadoHidrico {
  estado_general: string;
  total_sensores: number;
  total_alertas: number;
  alertas_criticas: number;
  alertas_advertencia: number;
  sensores_por_componente: Record<string, number>;
  ultimo_reporte: number;
  sensores: SensorReading[];
  alertas: AlertaHidrica[];
}

interface WeatherData {
  current?: {
    temperature_2m?: number;
    relative_humidity_2m?: number;
    precipitation?: number;
    rain?: number;
    weather_code?: number;
    wind_speed_10m?: number;
  };
  daily?: {
    time?: string[];
    precipitation_sum?: number[];
    rain_sum?: number[];
    temperature_2m_max?: number[];
    temperature_2m_min?: number[];
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ESTADO_COLORS: Record<string, string> = {
  operativo: '#22c55e',
  advertencia: '#f59e0b',
  critico: '#ef4444',
  sin_datos: '#6b7280',
};

const ESTADO_LABELS: Record<string, string> = {
  operativo: 'OPERATIVO',
  advertencia: 'ADVERTENCIA',
  critico: 'CRÍTICO',
  sin_datos: 'SIN DATOS',
};

const COMPONENTE_ICONS: Record<string, typeof Droplets> = {
  embalse: Waves,
  tunel: Activity,
  planta: Droplets,
  estacion_bombeo: Zap,
  red_distribucion: Gauge,
  rio: Waves,
  tanque: Droplets,
};

const UNIDAD_LABELS: Record<string, string> = {
  metros: 'm',
  psi: 'PSI',
  lps: 'L/s',
  ntu: 'NTU',
  ph: 'pH',
  mg_l: 'mg/L',
  celsius: '°C',
};

function timeAgo(ts: number): string {
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return `${Math.round(diff)}s`;
  if (diff < 3600) return `${Math.round(diff / 60)}m`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h`;
  return `${Math.round(diff / 86400)}d`;
}

function getWeatherIcon(code?: number): string {
  if (!code) return '🌤️';
  if (code <= 3) return '☀️';
  if (code <= 48) return '☁️';
  if (code <= 67) return '🌧️';
  if (code <= 77) return '❄️';
  if (code <= 82) return '🌦️';
  if (code <= 86) return '🌨️';
  return '⛈️';
}

// ---------------------------------------------------------------------------
// Sparkline mini-chart
// ---------------------------------------------------------------------------

function Sparkline({ values, color = '#22d3ee', height = 24, width = 80 }: {
  values: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (!values || values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="inline-block align-middle">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Gauge component for reservoir level
// ---------------------------------------------------------------------------

function ReservoirGauge({ nivel, min, max }: { nivel: number; min: number; max: number }) {
  const range = max - min || 1;
  const pct = Math.max(0, Math.min(100, ((nivel - min) / range) * 100));
  const color = pct > 60 ? '#22c55e' : pct > 30 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative w-full h-6 bg-[#0d1117] border border-cyan-900/40 overflow-hidden">
      <motion.div
        className="absolute inset-y-0 left-0"
        style={{ backgroundColor: color, opacity: 0.7 }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 1, ease: 'easeOut' }}
      />
      <div className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-bold text-white mix-blend-difference">
        {nivel.toFixed(1)} m ({pct.toFixed(0)}%)
      </div>
      {/* Min/max labels */}
      <div className="absolute bottom-[-14px] left-0 text-[8px] text-[var(--text-muted)] font-mono">{min}m</div>
      <div className="absolute bottom-[-14px] right-0 text-[8px] text-[var(--text-muted)] font-mono">{max}m</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function HidricoPanel({
  onFlyTo,
  isMinimized,
  onMinimizedChange,
}: {
  onFlyTo?: (lat: number, lng: number) => void;
  isMinimized?: boolean;
  onMinimizedChange?: (minimized: boolean) => void;
}) {
  const [estado, setEstado] = useState<EstadoHidrico | null>(null);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>('sensores');

  const fetchEstado = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hidrico/estado`);
      if (res.ok) {
        const data = await res.json();
        setEstado(data);
      }
    } catch (e) {
      console.warn('Failed to fetch hidrico estado', e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWeather = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hidrico/precipitacion`);
      if (res.ok) {
        setWeather(await res.json());
      }
    } catch (e) {
      console.warn('Failed to fetch weather', e);
    }
  }, []);

  useEffect(() => {
    fetchEstado();
    fetchWeather();
    const interval = setInterval(fetchEstado, 15000); // Poll every 15s
    const weatherInterval = setInterval(fetchWeather, 600000); // Weather every 10min
    return () => {
      clearInterval(interval);
      clearInterval(weatherInterval);
    };
  }, [fetchEstado, fetchWeather]);

  const statusColor = ESTADO_COLORS[estado?.estado_general || 'sin_datos'] || '#6b7280';
  const statusLabel = ESTADO_LABELS[estado?.estado_general || 'sin_datos'] || 'SIN DATOS';

  // Find reservoir level from sensors
  const nivelEmbalse = useMemo(() => {
    if (!estado?.sensores) return null;
    const sensor = estado.sensores.find(
      s => s.componente === 'embalse' && s.tipo_medicion === 'nivel'
    );
    return sensor?.valor ?? null;
  }, [estado]);

  // Last 7 days precipitation totals
  const precipLast7d = useMemo(() => {
    if (!weather?.daily?.precipitation_sum) return null;
    const sums = weather.daily.precipitation_sum;
    return sums.slice(-7).reduce((a, b) => a + (b || 0), 0);
  }, [weather]);

  const minimized = isMinimized ?? false;

  const toggleSection = (section: string) => {
    setExpandedSection(prev => prev === section ? null : section);
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6 }}
      className="bg-[#0a0a0a]/90 backdrop-blur-sm border border-cyan-900/40 pointer-events-auto overflow-hidden"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-cyan-950/30 transition-colors border-b border-cyan-900/40"
        onClick={() => onMinimizedChange?.(!minimized)}
      >
        <div className="flex items-center gap-2">
          <Droplets size={16} className="text-cyan-400" />
          <span className="text-[12px] text-cyan-400 font-mono tracking-widest font-bold">
            SISTEMA HÍDRICO
          </span>
          {/* Status badge */}
          <span
            className="text-[9px] font-mono px-1.5 py-0.5 border tracking-wider font-bold"
            style={{
              color: statusColor,
              borderColor: statusColor + '60',
              backgroundColor: statusColor + '15',
            }}
          >
            {statusLabel}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); fetchEstado(); }}
            className="w-6 h-6 flex items-center justify-center text-cyan-400/60 hover:text-cyan-300 transition-colors"
            title="Actualizar"
          >
            <RefreshCw size={12} />
          </button>
          {minimized ? <Plus size={16} className="text-cyan-400" /> : <Minus size={16} className="text-cyan-400" />}
        </div>
      </div>

      <AnimatePresence>
        {!minimized && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 flex flex-col gap-3">

              {/* ── RESERVOIR LEVEL GAUGE ── */}
              {nivelEmbalse !== null && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Waves size={12} className="text-cyan-400" />
                    <span className="text-[10px] font-mono tracking-wider text-cyan-400 font-bold">
                      NIVEL DEL EMBALSE
                    </span>
                  </div>
                  <ReservoirGauge nivel={nivelEmbalse} min={245} max={280} />
                  <div className="h-3" /> {/* spacer for min/max labels */}
                </div>
              )}

              {/* ── QUICK STATS ROW ── */}
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-[#0d1117] border border-cyan-900/30 p-2 text-center">
                  <div className="text-[9px] text-[var(--text-muted)] font-mono tracking-wider">SENSORES</div>
                  <div className="text-[16px] text-cyan-400 font-mono font-bold">
                    {estado?.total_sensores ?? '—'}
                  </div>
                </div>
                <div className="bg-[#0d1117] border border-cyan-900/30 p-2 text-center">
                  <div className="text-[9px] text-[var(--text-muted)] font-mono tracking-wider">ALERTAS</div>
                  <div
                    className="text-[16px] font-mono font-bold"
                    style={{ color: (estado?.total_alertas || 0) > 0 ? '#f59e0b' : '#22c55e' }}
                  >
                    {estado?.total_alertas ?? 0}
                  </div>
                </div>
                <div className="bg-[#0d1117] border border-cyan-900/30 p-2 text-center">
                  <div className="text-[9px] text-[var(--text-muted)] font-mono tracking-wider">LLUVIA 7D</div>
                  <div className="text-[16px] text-cyan-400 font-mono font-bold">
                    {precipLast7d !== null ? `${precipLast7d.toFixed(0)}mm` : '—'}
                  </div>
                </div>
              </div>

              {/* ── WEATHER ── */}
              {weather?.current && (
                <div
                  className="bg-[#0d1117]/80 border border-cyan-900/30 p-2 cursor-pointer hover:border-cyan-500/40 transition-colors"
                  onClick={() => toggleSection('clima')}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <CloudRain size={12} className="text-cyan-400" />
                      <span className="text-[10px] font-mono tracking-wider text-cyan-400 font-bold">CLIMA — TURIMIQUIRE</span>
                    </div>
                    {expandedSection === 'clima' ? <ChevronUp size={12} className="text-cyan-400" /> : <ChevronDown size={12} className="text-cyan-400" />}
                  </div>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-lg">{getWeatherIcon(weather.current.weather_code)}</span>
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--text-secondary)]">
                      <Thermometer size={10} className="text-orange-400" />
                      {weather.current.temperature_2m?.toFixed(1)}°C
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--text-secondary)]">
                      <Droplets size={10} className="text-blue-400" />
                      {weather.current.relative_humidity_2m}%
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--text-secondary)]">
                      <CloudRain size={10} className="text-cyan-400" />
                      {weather.current.precipitation?.toFixed(1)} mm
                    </div>
                  </div>
                  <AnimatePresence>
                    {expandedSection === 'clima' && weather.daily && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="mt-2 pt-2 border-t border-cyan-900/30"
                      >
                        <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 tracking-wider">PRECIPITACIÓN DIARIA (10 DÍAS)</div>
                        {weather.daily.precipitation_sum && (
                          <div className="flex items-end gap-0.5 h-8">
                            {weather.daily.precipitation_sum.map((v, i) => {
                              const max = Math.max(...(weather.daily?.precipitation_sum || [1]));
                              const h = max > 0 ? (v / max) * 100 : 0;
                              return (
                                <div
                                  key={i}
                                  className="flex-1 bg-cyan-500/50 hover:bg-cyan-400/70 transition-colors relative group"
                                  style={{ height: `${Math.max(h, 2)}%` }}
                                  title={`${weather.daily?.time?.[i] || ''}: ${v.toFixed(1)} mm`}
                                />
                              );
                            })}
                          </div>
                        )}
                        {weather.daily.time && (
                          <div className="flex justify-between mt-0.5">
                            <span className="text-[7px] font-mono text-[var(--text-muted)]">{weather.daily.time[0]}</span>
                            <span className="text-[7px] font-mono text-[var(--text-muted)]">{weather.daily.time[weather.daily.time.length - 1]}</span>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* ── ACTIVE ALERTS ── */}
              {(estado?.alertas?.length || 0) > 0 && (
                <div
                  className="bg-[#0d1117]/80 border border-amber-900/40 p-2 cursor-pointer hover:border-amber-500/40 transition-colors"
                  onClick={() => toggleSection('alertas')}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <AlertTriangle size={12} className="text-amber-400" />
                      <span className="text-[10px] font-mono tracking-wider text-amber-400 font-bold">
                        ALERTAS ({estado?.alertas?.length || 0})
                      </span>
                    </div>
                    {expandedSection === 'alertas' ? <ChevronUp size={12} className="text-amber-400" /> : <ChevronDown size={12} className="text-amber-400" />}
                  </div>
                  <AnimatePresence>
                    {expandedSection === 'alertas' && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="mt-2 flex flex-col gap-1"
                      >
                        {estado?.alertas?.map((a, i) => (
                          <div
                            key={i}
                            className="text-[10px] font-mono p-1.5 border"
                            style={{
                              color: a.tipo === 'critico' ? '#ef4444' : '#f59e0b',
                              borderColor: a.tipo === 'critico' ? '#ef444440' : '#f59e0b40',
                              backgroundColor: a.tipo === 'critico' ? '#ef444410' : '#f59e0b10',
                            }}
                          >
                            <span className="font-bold">{a.tipo === 'critico' ? '🔴' : '🟡'} {a.componente.toUpperCase()}</span>
                            <span className="text-[var(--text-secondary)] ml-1">— {a.mensaje}</span>
                            <span className="text-[var(--text-muted)] ml-1">{timeAgo(a.timestamp)}</span>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* ── SENSOR READINGS ── */}
              <div
                className="bg-[#0d1117]/80 border border-cyan-900/30 p-2 cursor-pointer hover:border-cyan-500/40 transition-colors"
                onClick={() => toggleSection('sensores')}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Gauge size={12} className="text-cyan-400" />
                    <span className="text-[10px] font-mono tracking-wider text-cyan-400 font-bold">
                      SENSORES EN TIEMPO REAL
                    </span>
                  </div>
                  {expandedSection === 'sensores' ? <ChevronUp size={12} className="text-cyan-400" /> : <ChevronDown size={12} className="text-cyan-400" />}
                </div>
                <AnimatePresence>
                  {expandedSection === 'sensores' && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-2 flex flex-col gap-1.5"
                    >
                      {estado?.sensores?.length ? (
                        estado.sensores.map((s) => {
                          const Icon = COMPONENTE_ICONS[s.componente] || Droplets;
                          const hasAlert = s.alertas && s.alertas.length > 0;
                          const alertType = s.alertas?.[0]?.tipo || '';
                          const borderColor = alertType === 'critico' ? '#ef444450' : alertType === 'advertencia' ? '#f59e0b50' : '#22d3ee30';
                          const valueColor = alertType === 'critico' ? '#ef4444' : alertType === 'advertencia' ? '#f59e0b' : '#22d3ee';

                          return (
                            <div
                              key={s.sensor_id}
                              className="flex items-center justify-between p-1.5 border hover:bg-cyan-950/20 transition-colors"
                              style={{ borderColor }}
                              onClick={(e) => {
                                e.stopPropagation();
                                if (s.lat && s.lng && onFlyTo) {
                                  onFlyTo(s.lat, s.lng);
                                }
                              }}
                            >
                              <div className="flex items-center gap-1.5 flex-1 min-w-0">
                                <Icon size={10} style={{ color: valueColor }} />
                                <div className="flex flex-col min-w-0">
                                  <span className="text-[9px] font-mono text-[var(--text-muted)] truncate tracking-wider">
                                    {s.componente.toUpperCase()} — {s.tipo_medicion}
                                  </span>
                                  <span className="text-[8px] font-mono text-[var(--text-muted)]">
                                    {s.sensor_id}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span
                                  className="text-[13px] font-mono font-bold tabular-nums"
                                  style={{ color: valueColor }}
                                >
                                  {s.valor.toFixed(1)}
                                </span>
                                <span className="text-[9px] font-mono text-[var(--text-muted)]">
                                  {UNIDAD_LABELS[s.unidad] || s.unidad}
                                </span>
                                {hasAlert && (
                                  <AlertTriangle
                                    size={10}
                                    className="animate-pulse"
                                    style={{ color: alertType === 'critico' ? '#ef4444' : '#f59e0b' }}
                                  />
                                )}
                                <span className="text-[8px] font-mono text-[var(--text-muted)]">
                                  {timeAgo(s.timestamp)}
                                </span>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="text-[10px] font-mono text-[var(--text-muted)] text-center py-2">
                          Sin datos de sensores — ejecuta el simulador
                          <br />
                          <code className="text-cyan-400 text-[9px]">python scripts/simulador_turimiquire.py</code>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* ── FLY TO INFRASTRUCTURE ── */}
              <div className="flex gap-1.5 flex-wrap">
                {[
                  { label: 'EMBALSE', lat: 10.133, lng: -63.933 },
                  { label: 'PLANTA', lat: 10.360, lng: -64.100 },
                  { label: 'CUMANÁ', lat: 10.456, lng: -64.167 },
                ].map(loc => (
                  <button
                    key={loc.label}
                    onClick={() => onFlyTo?.(loc.lat, loc.lng)}
                    className="text-[8px] font-mono tracking-wider px-2 py-1 border border-cyan-900/40 text-cyan-400/70 hover:text-cyan-300 hover:border-cyan-500/40 hover:bg-cyan-950/30 transition-all"
                  >
                    📍 {loc.label}
                  </button>
                ))}
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
