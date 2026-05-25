import axios from 'axios';

export interface TelemetryData {
  foreground_app: string;
  ram_usage: number;
  cpu_usage: number;
  battery_level: number;
  timestamp: number;
}

export interface PredictionData {
  predicted_apps: string[];
  confidence_scores: number[];
  method: string;
}

export interface AllocationData {
  action: string;
  target_app: string;
  cache_tier: string;
  reason: string;
}

export interface MetricsData {
  total_telemetry_records: number;
  average_ram_usage: number;
  average_battery_level: number;
  average_cpu_usage: number;
  cache_hit_rate: number;
  last_updated: string;
}

export interface BenchmarkData {
  lru_latency: number;
  ramwise_latency: number;
  lru_cache_hit_rate: number;
  ramwise_cache_hit_rate: number;
  lru_thrashing: number;
  ramwise_thrashing: number;
  latency_improvement_percent: number;
  cache_improvement_percent: number;
  thrashing_improvement_percent: number;
}

const BASE_URL = "http://localhost:8000";

export async function postTelemetry(data: TelemetryData): Promise<void> {
  await axios.post(`${BASE_URL}/telemetry`, data);
}

export async function getPredictions(appSequence: string): Promise<PredictionData> {
  const response = await axios.get(`${BASE_URL}/predict?app_sequence=${appSequence}`);
  return response.data;
}

export async function getAllocation(appSequence: string, ramUsage: number, batteryLevel: number): Promise<AllocationData> {
  const response = await axios.get(`${BASE_URL}/allocate?app_sequence=${appSequence}&ram_usage=${ramUsage}&battery_level=${batteryLevel}`);
  return response.data;
}

export async function getMetrics(): Promise<MetricsData> {
  const response = await axios.get(`${BASE_URL}/metrics`);
  return response.data;
}

export async function getBenchmark(): Promise<BenchmarkData> {
  const response = await axios.get(`${BASE_URL}/benchmark`);
  return response.data;
}
