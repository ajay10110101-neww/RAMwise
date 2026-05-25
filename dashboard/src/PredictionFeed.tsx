import { useEffect, useState, useRef } from "react";
import axios from "axios";

const SEED_SEQUENCES: string[][] = [
  ["client", "cms", "home"],
  ["music", "camera", "gallery"],
  ["whatsapp", "contacts", "dialer"],
  ["youtube", "music", "firefox"],
  ["maps", "weather", "calendar"],
  ["mail", "client", "cms"],
  ["camera", "gallery", "home"],
  ["dialer", "whatsapp", "contacts"],
];

const CHAIN_STEPS = 6;
const INTERVAL_MS = 2500;
const MAX_FEED = 25;
const SEQ_LEN = 7;

interface PredictionEntry {
  timestamp: string;
  input: string[];
  predicted: string[];
  confidence: number[];
  method: string;
  isSeed: boolean;
}

export default function PredictionFeed() {
  const [feed, setFeed] = useState<PredictionEntry[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  const seedIdx = useRef(0);
  const chainStep = useRef(0);
  const currentSeq = useRef<string[]>([...SEED_SEQUENCES[0]]);

  useEffect(() => {
    const interval = setInterval(async () => {
      const seq = currentSeq.current;
      const seqStr = seq.join(",");
      const isSeed = chainStep.current === 0;

      try {
        const res = await axios.get(`http://localhost:8000/predict`, {
          params: { app_sequence: seqStr },
        });

        const entry: PredictionEntry = {
          timestamp: new Date().toLocaleTimeString(),
          input: [...seq],
          predicted: res.data.predicted_apps,
          confidence: res.data.confidence_scores,
          method: res.data.method,
          isSeed,
        };

        setFeed((prev) => [entry, ...prev].slice(0, MAX_FEED));
        setTotalCount((c) => c + 1);

        const currentApps = currentSeq.current;
        let chosenApp = res.data.predicted_apps[0];
        for (const candidate of res.data.predicted_apps) {
          if (!currentApps.includes(candidate)) {
            chosenApp = candidate;
            break;
          }
        }
        const nextSeq = [...currentApps, chosenApp].slice(-SEQ_LEN);
        currentSeq.current = nextSeq;
      } catch (e) {
        console.error(e);
      }

      chainStep.current += 1;
      if (chainStep.current >= CHAIN_STEPS) {
        chainStep.current = 0;
        seedIdx.current = (seedIdx.current + 1) % SEED_SEQUENCES.length;
        currentSeq.current = [...SEED_SEQUENCES[seedIdx.current]];
      }
    }, INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ fontFamily: "monospace", padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#e0e0e0" }}>Chaining Prediction Feed</h3>
        <span style={{ color: "#888", fontSize: 12 }}>
          {totalCount} predictions | {SEED_SEQUENCES.length} seeds
        </span>
      </div>

      {feed.map((entry, i) => (
        <div
          key={i}
          style={{
            borderLeft: `3px solid ${entry.isSeed ? "#2196f3" : "#4caf50"}`,
            marginBottom: 10,
            paddingLeft: 12,
            opacity: 1 - i * 0.035,
            background: i === 0 ? "rgba(255,255,255,0.03)" : "transparent",
            borderRadius: 4,
            padding: "8px 12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span style={{ color: "#888", fontSize: 11 }}>{entry.timestamp}</span>
            <span
              style={{
                background: entry.isSeed ? "#1565c0" : "#2e7d32",
                color: "#fff",
                padding: "1px 6px",
                borderRadius: 8,
                fontSize: 10,
              }}
            >
              {entry.isSeed ? "🌱 seed" : "⛓ chain"}
            </span>
          </div>

          <div style={{ marginBottom: 4 }}>
            {entry.input.map((app, j) => (
              <span key={j}>
                <span style={{ color: "#ccc", fontSize: 12 }}>{app}</span>
                {j < entry.input.length - 1 && (
                  <span style={{ color: "#555", margin: "0 4px" }}>→</span>
                )}
              </span>
            ))}
          </div>

          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 4 }}>
            {entry.predicted.map((app, j) => (
              <span
                key={j}
                style={{
                  background: j === 0 ? "#1b5e20" : "#2e2e2e",
                  color: "#fff",
                  padding: "2px 8px",
                  borderRadius: 4,
                  fontSize: 11,
                }}
              >
                {app} {(entry.confidence[j] * 100).toFixed(1)}%
              </span>
            ))}
          </div>

          <span
            style={{
              fontSize: 10,
              color: entry.method === "transformer" ? "#4caf50" : "#ff9800",
            }}
          >
            via {entry.method}
          </span>
        </div>
      ))}
    </div>
  );
}
