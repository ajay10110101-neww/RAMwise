import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { getPredictions, getAllocation, getMetrics, getBenchmark, postTelemetry } from './api';
import type { PredictionData, AllocationData, MetricsData, BenchmarkData } from './api';
import PredictionFeed from './PredictionFeed';

const APP_SEQUENCE = ["client", "cms", "home", "music", "camera", "gallery", "contacts", "dialer", "browser", "whatsapp", "youtube", "maps", "weather", "calendar", "mail", "firefox", "gallery", "music", "client", "cms", "home", "contacts", "dialer", "camera", "whatsapp"];
const SEQUENCE_INTERVAL_MS = 3000;

const GLOBAL_STYLES = `
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}
@keyframes slideInLeft {
  from { transform: translateX(-30px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes fadeInUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes borderSweep {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes glow {
  0%, 100% { box-shadow: 0 0 5px currentColor; }
  50% { box-shadow: 0 0 20px currentColor, 0 0 40px currentColor; }
}
@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes warningFlash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

body {
  margin: 0;
  background: #0a0a14;
}

.ramwise-grid-bg {
  background-image: radial-gradient(circle, #1a1a2e 1px, transparent 1px);
  background-size: 24px 24px;
}

.card-border-animated {
  position: relative;
  border: none !important;
  overflow: hidden;
}
.card-border-animated::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  padding: 1.5px;
  background: linear-gradient(270deg, #00ff88, #4488ff, #ff8800, #00ff88);
  background-size: 300% 300%;
  animation: borderSweep 3s ease infinite;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

.glow-line-ram {
  filter: drop-shadow(0 0 4px #00ff88) drop-shadow(0 0 8px rgba(0,255,136,0.3));
}
.glow-line-cpu {
  filter: drop-shadow(0 0 4px #ff6b6b) drop-shadow(0 0 8px rgba(255,107,107,0.3));
}

.tier-active-glow {
  animation: slideInLeft 0.4s ease forwards;
}
.tier-inactive-scanlines {
  background-image: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(255,255,255,0.02) 2px,
    rgba(255,255,255,0.02) 4px
  );
}

.metric-spark {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 1.5s ease infinite;
}

.battery-warning {
  animation: warningFlash 0.8s ease infinite;
}
`;

function MetricsCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="card-border-animated" style={{ background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", flex: 1, margin: "0 8px", position: 'relative', border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: "8px" }}>
        <span className="metric-spark" style={{ background: color }} />
        <span style={{ color: "#666", fontSize: "0.7rem", letterSpacing: "0.05em", textTransform: "uppercase" }}>{label}</span>
      </div>
      <div style={{ color: color, fontSize: "1.5rem", fontWeight: "bold", fontFamily: "'JetBrains Mono', monospace" }}>{value}</div>
    </div>
  );
}

function CacheTierBox({ tier, label, color, isActive, app }: { tier: string; label: string; color: string; isActive: boolean; app: string }) {
  return (
    <div
      className={isActive ? "tier-active-glow" : "tier-inactive-scanlines"}
      style={{
        background: isActive ? `linear-gradient(135deg, ${color}22, ${color}44)` : "#16162a",
        border: `1px solid ${isActive ? color : '#222'}`,
        borderRadius: "8px",
        padding: "12px",
        marginBottom: "8px",
        opacity: isActive ? 1 : 0.4,
        color: isActive ? '#fff' : '#555',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div style={{ fontSize: "0.85rem", fontWeight: "bold", position: 'relative' }}>{label}</div>
      {isActive && <div style={{ fontSize: "0.75rem", marginTop: "4px", color: color, fontFamily: "'JetBrains Mono', monospace", position: 'relative' }}>{"->"} {app}</div>}
    </div>
  );
}

function PredictionRow({ app, confidence, rank }: { app: string; confidence: number; rank: number }) {
  const rankColors = ["#00ff88", "#4488ff", "#ff8800"];
  return (
    <div style={{ marginBottom: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{
            fontSize: "0.6rem",
            color: rankColors[rank],
            background: "rgba(255,255,255,0.05)",
            border: `1px solid ${rankColors[rank]}44`,
            borderRadius: "4px",
            padding: "1px 5px",
            fontWeight: "bold",
          }}>#{rank + 1}</span>
          <span style={{ fontSize: "0.8rem", color: "#ccc", wordBreak: "break-all" }}>{app}</span>
        </div>
        <span style={{ fontSize: "0.75rem", color: rankColors[rank], fontWeight: "bold", marginLeft: "8px", flexShrink: 0 }}>
          {(confidence * 100).toFixed(1)}%
        </span>
      </div>
      <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: "4px", height: "6px", width: "100%" }}>
        <div style={{
          background: rankColors[rank],
          height: "100%",
          borderRadius: "4px",
          width: `${confidence * 100}%`,
          transition: "width 0.6s ease",
        }} />
      </div>
    </div>
  );
}

function BatteryIcon({ level }: { level: number }) {
  const segments = 5;
  const filledCount = Math.ceil((level / 100) * segments);
  const color = level < 30 ? "#ff4444" : level < 60 ? "#ff8800" : "#00ff88";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 2, marginRight: 12 }}>
      {Array.from({ length: segments }).map((_, i) => (
        <div
          key={i}
          style={{
            width: 8,
            height: 16 + i * 2,
            borderRadius: 2,
            background: i < filledCount ? color : "#222",
            border: `1px solid ${i < filledCount ? color : '#333'}`,
            transition: "all 0.3s ease",
            boxShadow: i < filledCount ? `0 0 4px ${color}44` : "none",
          }}
        />
      ))}
      <div style={{ width: 3, height: 8, background: level > 0 ? color : '#222', borderRadius: '0 2px 2px 0', marginLeft: 1 }} />
    </div>
  );
}

function App() {
  const [ramHistory, setRamHistory] = useState<{ time: string; ram: number; cpu: number }[]>([]);
  const [predictions, setPredictions] = useState<PredictionData | null>(null);
  const [allocation, setAllocation] = useState<AllocationData | null>(null);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [batteryLevel, setBatteryLevel] = useState<number>(60);
  const [currentAppIndex, setCurrentAppIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const indexRef = useRef(0);

  useEffect(() => {
    async function fetchInitialData() {
      try {
        const [metricsData, benchmarkData] = await Promise.all([getMetrics(), getBenchmark()]);
        setMetrics(metricsData);
        setBenchmark(benchmarkData);
        setLoading(false);
      } catch {
        setError("Failed to connect to RAMWise backend. Make sure the server is running at localhost:8000");
        setLoading(false);
      }
    }
    fetchInitialData();
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      const idx = indexRef.current;
      const currentApp = APP_SEQUENCE[idx % APP_SEQUENCE.length];
      const nextApp = APP_SEQUENCE[(idx + 1) % APP_SEQUENCE.length];
      const thirdApp = APP_SEQUENCE[(idx + 2) % APP_SEQUENCE.length];
      const appSeqString = `${currentApp},${nextApp},${thirdApp}`;

      const ramValue = 45 + Math.floor(Math.random() * 40);
      const cpuValue = 20 + Math.floor(Math.random() * 50);

      try {
        await postTelemetry({
          foreground_app: currentApp,
          ram_usage: ramValue,
          cpu_usage: cpuValue,
          battery_level: batteryLevel,
          timestamp: Math.floor(Date.now() / 1000),
        });

        const [predData, allocData, metricsData] = await Promise.all([
          getPredictions(appSeqString),
          getAllocation(appSeqString, ramValue, batteryLevel),
          getMetrics(),
        ]);

        setPredictions(predData);
        setAllocation(allocData);
        setMetrics(metricsData);

        setRamHistory(prev => {
          const newHistory = [...prev, { time: new Date().toLocaleTimeString(), ram: ramValue, cpu: cpuValue }];
          if (newHistory.length > 20) {
            return newHistory.slice(newHistory.length - 20);
          }
          return newHistory;
        });
      } catch (err) {
        console.error("API call failed:", err);
      }

      indexRef.current = idx + 1;
      setCurrentAppIndex(idx + 1);
    }, SEQUENCE_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [batteryLevel]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "linear-gradient(135deg, #0a0a14 0%, #0d0d1a 50%, #0a0f1a 100%)", color: "#e0e0e0", fontFamily: "'JetBrains Mono', monospace" }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: "1.5rem", marginBottom: 12, color: "#00ff88" }}>RAMWise</div>
          <div style={{ color: "#555", fontSize: "0.85rem" }}>Initializing dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "linear-gradient(135deg, #0a0a14 0%, #0d0d1a 50%, #0a0f1a 100%)", color: "#ff4444", fontFamily: "'JetBrains Mono', monospace", flexDirection: "column", padding: "20px" }}>
        <div style={{ fontSize: "1.2rem", marginBottom: "12px" }}>{error}</div>
        <div style={{ color: "#555", fontSize: "0.85rem" }}>Run: uvicorn api.main:app --reload --port 8000</div>
      </div>
    );
  }

  const actionColor = allocation
    ? allocation.action === "preload_app"
      ? "#00ff88"
      : allocation.action === "evict_app"
      ? "#ff4444"
      : allocation.action === "move_to_hot"
      ? "#ff8800"
      : "#4488ff"
    : "#4488ff";

  const latestRam = ramHistory.length > 0 ? ramHistory[ramHistory.length - 1].ram : 0;
  const latestCpu = ramHistory.length > 0 ? ramHistory[ramHistory.length - 1].cpu : 0;

  return (
    <div className="ramwise-grid-bg" style={{ fontFamily: "'JetBrains Mono', monospace", background: "linear-gradient(135deg, #0a0a14 0%, #0d0d1a 50%, #0a0f1a 100%)", minHeight: "100vh", color: "#e0e0e0", padding: "20px" }}>
      <style>{GLOBAL_STYLES}</style>

      {/* HEADER */}
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
        <h1 style={{ color: "#00ff88", fontSize: "2rem", margin: 0, letterSpacing: '0.05em' }}>RAMWise</h1>
        <p style={{ color: "#555", margin: "8px 0 0 0", fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase" }}>Context-Aware Adaptive Memory Management</p>
      </div>

      {/* METRICS ROW */}
      <div style={{ display: "flex", marginBottom: "20px" }}>
        <MetricsCard label="Total Records" value={String(metrics?.total_telemetry_records ?? 0)} color="#4488ff" />
        <MetricsCard label="Avg RAM Usage" value={`${(metrics?.average_ram_usage ?? 0).toFixed(1)}%`} color="#00ff88" />
        <MetricsCard label="Cache Hit Rate" value={`${((metrics?.cache_hit_rate ?? 0) * 100).toFixed(1)}%`} color="#ff8800" />
        <MetricsCard label="Avg Battery" value={`${(metrics?.average_battery_level ?? 0).toFixed(1)}%`} color="#ff6b6b" />
      </div>

      {/* LIVE CHART */}
      <div style={{ background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: "12px" }}>
          <span style={{ color: "#888", fontSize: "0.85rem", letterSpacing: "0.05em" }}>Live RAM & CPU Usage</span>
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{ color: "#00ff88", fontSize: "0.75rem", fontFamily: "'JetBrains Mono', monospace" }}>RAM: {latestRam}%</span>
            <span style={{ color: "#ff6b6b", fontSize: "0.75rem", fontFamily: "'JetBrains Mono', monospace" }}>CPU: {latestCpu}%</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={ramHistory}>
            <CartesianGrid stroke="#1a1a2e" />
            <XAxis dataKey="time" stroke="#444" tick={{ fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }} />
            <YAxis domain={[0, 100]} stroke="#444" tick={{ fontSize: 9 }} />
            <Tooltip contentStyle={{ background: "rgba(10,10,20,0.9)", border: "1px solid #333", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }} />
            <Line className="glow-line-ram" type="monotone" dataKey="ram" stroke="#00ff88" strokeWidth={2} dot={false} name="RAM %" />
            <Line className="glow-line-cpu" type="monotone" dataKey="cpu" stroke="#ff6b6b" strokeWidth={2} dot={false} name="CPU %" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* MIDDLE ROW */}
      <div style={{ display: "flex", marginBottom: "20px" }}>
        {/* CACHE TIERS */}
        <div style={{ flex: 1, background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", margin: "0 8px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
          <div style={{ color: "#888", fontSize: "0.85rem", marginBottom: "12px", letterSpacing: "0.05em" }}>Cache Tiers</div>
          <CacheTierBox tier="HOT" label={`\uD83D\uDD25 HOT \u2014 Fully Active in RAM`} color="#ff4444" isActive={allocation?.cache_tier === "HOT"} app={allocation?.target_app ?? ""} />
          <CacheTierBox tier="WARM" label={`\uD83C\uDF21\uFE0F WARM \u2014 Partially Retained`} color="#ff8800" isActive={allocation?.cache_tier === "WARM"} app={allocation?.target_app ?? ""} />
          <CacheTierBox tier="COLD" label={`\u2744\uFE0F COLD \u2014 Evicted from Active Memory`} color="#4444ff" isActive={allocation?.cache_tier === "COLD"} app={allocation?.target_app ?? ""} />
        </div>

        {/* PREDICTIONS */}
        <div style={{ flex: 1, background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", margin: "0 8px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
          <div style={{ color: "#888", fontSize: "0.85rem", marginBottom: "12px", letterSpacing: "0.05em" }}>
            Next App Predictions
            {predictions && (
              <span style={{ background: "#1a2a1a", border: "1px solid #00ff8833", borderRadius: "12px", padding: "2px 8px", fontSize: "0.6rem", marginLeft: "8px", color: "#00ff88", fontFamily: "'JetBrains Mono', monospace" }}>
                {predictions.method}
              </span>
            )}
          </div>
          {predictions ? (
            predictions.predicted_apps.map((app, i) => (
              <PredictionRow key={app} app={app} confidence={predictions.confidence_scores[i] ?? 0} rank={i} />
            ))
          ) : (
            <div style={{ color: "#444", fontSize: "0.8rem" }}>Waiting for data...</div>
          )}
        </div>

        {/* RL DECISION */}
        <div style={{
          flex: 1,
          background: allocation
            ? allocation.cache_tier === "HOT"
              ? "rgba(255, 68, 68, 0.08)"
              : allocation.cache_tier === "WARM"
              ? "rgba(255, 136, 0, 0.08)"
              : "rgba(68, 68, 255, 0.08)"
            : "rgba(255,255,255,0.04)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          borderRadius: "8px",
          padding: "16px",
          margin: "0 8px",
          border: allocation
            ? allocation.cache_tier === "HOT"
              ? "1px solid rgba(255, 68, 68, 0.25)"
              : allocation.cache_tier === "WARM"
              ? "1px solid rgba(255, 136, 0, 0.25)"
              : "1px solid rgba(68, 68, 255, 0.25)"
            : "1px solid rgba(255,255,255,0.08)",
          transition: "background 0.6s ease, border 0.6s ease",
        }}>
          <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>RL Memory Decision</div>
          {allocation ? (
            <div>
              <div style={{ color: actionColor, fontSize: "1.1rem", fontWeight: "bold", marginBottom: "8px", letterSpacing: "0.05em" }}>
                {allocation.action.replace(/_/g, " ").toUpperCase()}
              </div>
              <div style={{ fontSize: "0.9rem", marginBottom: "8px", color: "#ccc" }}>{"->"} {allocation.target_app}</div>
              <div style={{
                display: "inline-block",
                background: allocation.cache_tier === "HOT"
                  ? "rgba(255,68,68,0.2)"
                  : allocation.cache_tier === "WARM"
                  ? "rgba(255,136,0,0.2)"
                  : "rgba(68,68,255,0.2)",
                border: allocation.cache_tier === "HOT"
                  ? "1px solid rgba(255,68,68,0.5)"
                  : allocation.cache_tier === "WARM"
                  ? "1px solid rgba(255,136,0,0.5)"
                  : "1px solid rgba(68,68,255,0.5)",
                borderRadius: "12px",
                padding: "2px 10px",
                fontSize: "0.75rem",
                marginBottom: "8px",
                color: allocation.cache_tier === "HOT" ? "#ff6666" : allocation.cache_tier === "WARM" ? "#ffaa44" : "#6688ff",
                fontWeight: "600",
                letterSpacing: "0.08em",
              }}>
                {allocation.cache_tier}
              </div>
              <div style={{ color: "#777", fontSize: "0.72rem", fontStyle: "italic", marginTop: "8px", lineHeight: "1.5" }}>
                {allocation.reason}
              </div>
            </div>
          ) : (
            <div style={{ color: "#666", fontSize: "0.8rem" }}>Waiting for RL decision...</div>
          )}
        </div>
      </div>

      {/* BATTERY SLIDER */}
      <div style={{ background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
        <div style={{ color: "#888", fontSize: "0.85rem", marginBottom: "12px", letterSpacing: "0.05em" }}>Battery Level Simulation</div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <BatteryIcon level={batteryLevel} />
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={batteryLevel}
            onChange={(e) => setBatteryLevel(Number(e.target.value))}
            className={batteryLevel < 30 ? "battery-warning" : ""}
            style={{ flex: 1, accentColor: batteryLevel < 30 ? "#ff4444" : batteryLevel < 60 ? "#ff8800" : "#00ff88" }}
          />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px" }}>
          <span style={{ color: batteryLevel < 30 ? "#ff4444" : batteryLevel < 60 ? "#ff8800" : "#00ff88", fontWeight: "bold", fontFamily: "'JetBrains Mono', monospace" }}>
            Battery: {batteryLevel}%
          </span>
          <span style={{ color: "#444", fontSize: "0.7rem" }}>Adjust battery to see how RAMWise adapts allocation strategy</span>
        </div>
      </div>

      {/* BENCHMARK */}
      <div style={{ background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
        <div style={{ color: "#888", fontSize: "0.85rem", marginBottom: "12px", letterSpacing: "0.05em" }}>RAMWise vs LRU Benchmark</div>
        {benchmark ? (
          <div>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px", flexWrap: 'wrap' }}>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.7rem", color: "#00ff88", fontFamily: "'JetBrains Mono', monospace" }}>
                {"\u2705"} LATENCY: -{benchmark.latency_improvement_percent}%
              </span>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.7rem", color: "#00ff88", fontFamily: "'JetBrains Mono', monospace" }}>
                {"\u2705"} HIT RATE: +{benchmark.cache_improvement_percent}%
              </span>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.7rem", color: "#00ff88", fontFamily: "'JetBrains Mono', monospace" }}>
                {"\u2705"} THRASHING: -{benchmark.thrashing_improvement_percent}%
              </span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { metric: "Launch Latency (s)", LRU: benchmark.lru_latency, RAMWise: benchmark.ramwise_latency },
                { metric: "Cache Hit Rate", LRU: benchmark.lru_cache_hit_rate, RAMWise: benchmark.ramwise_cache_hit_rate },
                { metric: "Thrashing Rate", LRU: benchmark.lru_thrashing, RAMWise: benchmark.ramwise_thrashing },
              ]}>
                <CartesianGrid stroke="#1a1a2e" />
                <XAxis dataKey="metric" stroke="#555" tick={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }} />
                <YAxis stroke="#555" tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ background: "rgba(10,10,20,0.9)", border: "1px solid #333", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }} />
                <defs>
                  <linearGradient id="gradLru" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ff4444" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#ff4444" stopOpacity={0.2} />
                  </linearGradient>
                  <linearGradient id="gradRamwise" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00ff88" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#00ff88" stopOpacity={0.2} />
                  </linearGradient>
                </defs>
                <Bar dataKey="LRU" fill="url(#gradLru)" />
                <Bar dataKey="RAMWise" fill="url(#gradRamwise)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ color: "#444", fontSize: "0.8rem" }}>Loading benchmark data...</div>
        )}
      </div>

      {/* PREDICTION FEED */}
      <div style={{ background: "rgba(255,255,255,0.04)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
        <PredictionFeed />
      </div>

      <p style={{ textAlign: "center", color: "#333", marginTop: "40px", fontSize: "0.7rem", letterSpacing: "0.1em" }}>RAMWise -- Context-Aware Adaptive Memory Management | FastAPI + PyTorch + PPO + React</p>
    </div>
  );
}

export default App;
