import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { getPredictions, getAllocation, getMetrics, getBenchmark, postTelemetry } from './api';
import type { PredictionData, AllocationData, MetricsData, BenchmarkData } from './api';

const APP_SEQUENCE = ["Chrome", "WhatsApp", "Instagram", "Spotify", "YouTube", "Maps", "Gmail", "Twitter", "Netflix", "Camera"];
const SEQUENCE_INTERVAL_MS = 3000;

function MetricsCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ background: "#1a1a2e", borderRadius: "8px", padding: "16px", flex: 1, margin: "0 8px", border: "1px solid #333" }}>
      <div style={{ color: "#888", fontSize: "0.75rem", marginBottom: "8px" }}>{label}</div>
      <div style={{ color: color, fontSize: "1.5rem", fontWeight: "bold" }}>{value}</div>
    </div>
  );
}

function CacheTierBox({ tier, label, color, isActive, app }: { tier: string; label: string; color: string; isActive: boolean; app: string }) {
  return (
    <div style={{
      background: isActive ? color : "#2a1a1a",
      border: `2px solid ${color}`,
      borderRadius: "8px",
      padding: "12px",
      marginBottom: "8px",
      opacity: isActive ? 1 : 0.5,
    }}>
      <div style={{ fontSize: "0.85rem", fontWeight: "bold" }}>{label}</div>
      {isActive && <div style={{ fontSize: "0.75rem", marginTop: "4px" }}>→ {app}</div>}
    </div>
  );
}

function PredictionRow({ app, confidence }: { app: string; confidence: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: "8px" }}>
      <div style={{ width: "80px", fontSize: "0.8rem" }}>{app}</div>
      <div style={{ flex: 1, background: "#333", borderRadius: "4px", height: "16px", marginRight: "8px" }}>
        <div style={{ background: "#00ff88", height: "100%", borderRadius: "4px", width: `${confidence * 100}%` }} />
      </div>
      <div style={{ width: "45px", fontSize: "0.75rem", textAlign: "right" }}>{(confidence * 100).toFixed(1)}%</div>
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
          getAllocation(currentApp, ramValue, batteryLevel),
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
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", backgroundColor: "#0f0f1a", color: "#e0e0e0", fontFamily: "monospace" }}>
        Loading RAMWise Dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", backgroundColor: "#0f0f1a", color: "#ff4444", fontFamily: "monospace", flexDirection: "column", padding: "20px" }}>
        <div style={{ fontSize: "1.2rem", marginBottom: "12px" }}>{error}</div>
        <div style={{ color: "#888", fontSize: "0.85rem" }}>Run: uvicorn api.main:app --reload --port 8000</div>
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

  return (
    <div style={{ fontFamily: "monospace", backgroundColor: "#0f0f1a", minHeight: "100vh", color: "#e0e0e0", padding: "20px" }}>
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
        <h1 style={{ color: "#00ff88", fontSize: "2rem", margin: 0 }}>RAMWise Dashboard</h1>
        <p style={{ color: "#888", margin: "8px 0 0 0" }}>Context-Aware Adaptive Memory Management</p>
      </div>

      <div style={{ display: "flex", marginBottom: "20px" }}>
        <MetricsCard label="Total Records" value={String(metrics?.total_telemetry_records ?? 0)} color="#4488ff" />
        <MetricsCard label="Avg RAM Usage" value={`${(metrics?.average_ram_usage ?? 0).toFixed(1)}%`} color="#00ff88" />
        <MetricsCard label="Cache Hit Rate" value={`${((metrics?.cache_hit_rate ?? 0) * 100).toFixed(1)}%`} color="#ff8800" />
        <MetricsCard label="Avg Battery" value={`${(metrics?.average_battery_level ?? 0).toFixed(1)}%`} color="#ff6b6b" />
      </div>

      <div style={{ background: "#1a1a2e", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid #333" }}>
        <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>Live RAM & CPU Usage</div>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={ramHistory}>
            <CartesianGrid stroke="#333" />
            <XAxis dataKey="time" stroke="#888" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 100]} stroke="#888" />
            <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }} />
            <Legend />
            <Line type="monotone" dataKey="ram" stroke="#00ff88" strokeWidth={2} dot={false} name="RAM %" />
            <Line type="monotone" dataKey="cpu" stroke="#ff6b6b" strokeWidth={2} dot={false} name="CPU %" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "flex", marginBottom: "20px" }}>
        <div style={{ flex: 1, background: "#1a1a2e", borderRadius: "8px", padding: "16px", margin: "0 8px", border: "1px solid #333" }}>
          <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>Cache Tiers</div>
          <CacheTierBox tier="HOT" label="🔴 HOT — Fully Active in RAM" color="#ff4444" isActive={allocation?.cache_tier === "HOT"} app={allocation?.target_app ?? ""} />
          <CacheTierBox tier="WARM" label="🟠 WARM — Partially Retained" color="#ff8800" isActive={allocation?.cache_tier === "WARM"} app={allocation?.target_app ?? ""} />
          <CacheTierBox tier="COLD" label="🔵 COLD — Evicted from Active Memory" color="#4444ff" isActive={allocation?.cache_tier === "COLD"} app={allocation?.target_app ?? ""} />
        </div>

        <div style={{ flex: 1, background: "#1a1a2e", borderRadius: "8px", padding: "16px", margin: "0 8px", border: "1px solid #333" }}>
          <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>
            Next App Predictions
            {predictions && (
              <span style={{ background: "#333", borderRadius: "12px", padding: "2px 8px", fontSize: "0.65rem", marginLeft: "8px" }}>
                {predictions.method}
              </span>
            )}
          </div>
          {predictions ? (
            predictions.predicted_apps.map((app, i) => (
              <PredictionRow key={app} app={app} confidence={predictions.confidence_scores[i] ?? 0} />
            ))
          ) : (
            <div style={{ color: "#666", fontSize: "0.8rem" }}>Waiting for data...</div>
          )}
        </div>

        <div style={{ flex: 1, background: "#1a1a2e", borderRadius: "8px", padding: "16px", margin: "0 8px", border: "1px solid #333" }}>
          <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>RL Memory Decision</div>
          {allocation ? (
            <div>
              <div style={{ color: actionColor, fontSize: "1.1rem", fontWeight: "bold", marginBottom: "8px" }}>
                {allocation.action.replace(/_/g, " ").toUpperCase()}
              </div>
              <div style={{ fontSize: "0.9rem", marginBottom: "8px" }}>→ {allocation.target_app}</div>
              <div style={{
                display: "inline-block",
                background: allocation.cache_tier === "HOT" ? "#ff4444" : allocation.cache_tier === "WARM" ? "#ff8800" : "#4444ff",
                borderRadius: "12px",
                padding: "2px 10px",
                fontSize: "0.75rem",
                marginBottom: "8px",
              }}>
                {allocation.cache_tier}
              </div>
              <div style={{ color: "#888", fontSize: "0.75rem", fontStyle: "italic", marginTop: "8px" }}>{allocation.reason}</div>
            </div>
          ) : (
            <div style={{ color: "#666", fontSize: "0.8rem" }}>Waiting for RL decision...</div>
          )}
        </div>
      </div>

      <div style={{ background: "#1a1a2e", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid #333" }}>
        <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>Battery Level Simulation</div>
        <input
          type="range"
          min={10}
          max={100}
          step={5}
          value={batteryLevel}
          onChange={(e) => setBatteryLevel(Number(e.target.value))}
          style={{ width: "100%", accentColor: batteryLevel < 30 ? "#ff4444" : batteryLevel < 60 ? "#ff8800" : "#00ff88" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px" }}>
          <span style={{ color: batteryLevel < 30 ? "#ff4444" : batteryLevel < 60 ? "#ff8800" : "#00ff88", fontWeight: "bold" }}>
            Battery: {batteryLevel}%
          </span>
          <span style={{ color: "#666", fontSize: "0.75rem" }}>Adjust battery to see how RAMWise adapts allocation strategy</span>
        </div>
      </div>

      <div style={{ background: "#1a1a2e", borderRadius: "8px", padding: "16px", marginBottom: "20px", border: "1px solid #333" }}>
        <div style={{ color: "#e0e0e0", fontSize: "0.9rem", marginBottom: "12px" }}>RAMWise vs LRU Benchmark</div>
        {benchmark ? (
          <div>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.75rem", color: "#00ff88" }}>
                Latency: -{benchmark.latency_improvement_percent}% faster
              </span>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.75rem", color: "#00ff88" }}>
                Cache: +{benchmark.cache_improvement_percent}% hit rate
              </span>
              <span style={{ background: "#0a2a0a", border: "1px solid #00ff88", borderRadius: "12px", padding: "4px 12px", fontSize: "0.75rem", color: "#00ff88" }}>
                Thrashing: -{benchmark.thrashing_improvement_percent}% reduction
              </span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { metric: "Launch Latency (s)", LRU: benchmark.lru_latency, RAMWise: benchmark.ramwise_latency },
                { metric: "Cache Hit Rate", LRU: benchmark.lru_cache_hit_rate, RAMWise: benchmark.ramwise_cache_hit_rate },
                { metric: "Thrashing Rate", LRU: benchmark.lru_thrashing, RAMWise: benchmark.ramwise_thrashing },
              ]}>
                <CartesianGrid stroke="#333" />
                <XAxis dataKey="metric" stroke="#888" tick={{ fontSize: 11 }} />
                <YAxis stroke="#888" />
                <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }} />
                <Legend />
                <Bar dataKey="LRU" fill="#ff4444" />
                <Bar dataKey="RAMWise" fill="#00ff88" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ color: "#666", fontSize: "0.8rem" }}>Loading benchmark data...</div>
        )}
      </div>

      <p style={{ textAlign: "center", color: "#444", marginTop: "40px" }}>RAMWise — Context-Aware Adaptive Memory Management | Built with FastAPI + PyTorch + PPO + React</p>
    </div>
  );
}

export default App;
