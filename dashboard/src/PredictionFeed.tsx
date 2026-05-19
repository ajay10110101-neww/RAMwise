import { useEffect, useState } from "react";
import axios from "axios";

const DEMO_SEQUENCES = [
  "chrome,whatsapp",
  "whatsapp,instagram",
  "youtube,spotify",
  "gmail,calendar",
  "maps,chrome",
  "instagram,camera",
  "spotify,youtube",
  "calculator,files",
];

interface PredictionEntry {
  timestamp: string;
  input: string;
  predicted: string[];
  confidence: number[];
  method: string;
}

export default function PredictionFeed() {
  const [feed, setFeed] = useState<PredictionEntry[]>([]);
  const [seqIndex, setSeqIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      const seq = DEMO_SEQUENCES[seqIndex % DEMO_SEQUENCES.length];
      try {
        const res = await axios.get(`/predict`, {
          params: { app_sequence: seq }
        });
        const entry: PredictionEntry = {
          timestamp: new Date().toLocaleTimeString(),
          input: seq,
          predicted: res.data.predicted_apps,
          confidence: res.data.confidence_scores,
          method: res.data.method,
        };
        setFeed(prev => [entry, ...prev].slice(0, 20));
        setSeqIndex(i => i + 1);
      } catch (e) {
        console.error(e);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [seqIndex]);

  return (
    <div style={{ fontFamily: "monospace", padding: 16 }}>
      <h3>Live Prediction Feed</h3>
      {feed.map((entry, i) => (
        <div key={i} style={{
          borderLeft: "3px solid #4caf50",
          marginBottom: 8,
          paddingLeft: 10,
          opacity: 1 - i * 0.04
        }}>
          <span style={{ color: "#888", fontSize: 11 }}>{entry.timestamp}</span>
          <span style={{ marginLeft: 8, color: "#aaa" }}>Input: {entry.input}</span>
          <div>
            {entry.predicted.map((app, j) => (
              <span key={j} style={{
                marginRight: 8,
                background: j === 0 ? "#1b5e20" : "#2e2e2e",
                color: "#fff",
                padding: "2px 8px",
                borderRadius: 4,
                fontSize: 12
              }}>
                {app} {(entry.confidence[j] * 100).toFixed(1)}%
              </span>
            ))}
          </div>
          <span style={{ fontSize: 10, color: entry.method === "transformer" ? "#4caf50" : "#ff9800" }}>
            via {entry.method}
          </span>
        </div>
      ))}
    </div>
  );
}
