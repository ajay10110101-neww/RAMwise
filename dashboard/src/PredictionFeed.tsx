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

const FEED_STYLES = `
@keyframes slideInDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes fadeGlow {
  0% { box-shadow: 0 0 15px rgba(0,255,136,0.5); border-left-color: #00ff88; }
  100% { box-shadow: none; border-left-color: #333; }
}
@keyframes shimmerFeed {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes chainPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.feed-entry-new {
  animation: slideInDown 0.4s ease forwards;
}
.feed-entry-glow {
  animation: fadeGlow 2s ease forwards;
}
.shimmer-top-badge {
  background: linear-gradient(90deg, #1b5e20 25%, #2e7d32 50%, #1b5e20 75%);
  background-size: 200% 100%;
  animation: shimmerFeed 2s infinite;
}
.chain-icon-pulse {
  animation: chainPulse 1.5s ease infinite;
}
.seed-glow {
  box-shadow: 0 0 8px rgba(76,175,80,0.4);
}
.chain-glow {
  box-shadow: 0 0 8px rgba(0,255,255,0.3);
}
.prediction-feed-scroll {
  overflow-y: auto;
  max-height: 600px;
}
.prediction-feed-scroll::-webkit-scrollbar { width: 6px; }
.prediction-feed-scroll::-webkit-scrollbar-track { background: #0a0a14; }
.prediction-feed-scroll::-webkit-scrollbar-thumb { background: #222; border-radius: 3px; }
`;

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
    <div style={{ fontFamily: "'JetBrains Mono', monospace", padding: 0 }}>
      <style>{FEED_STYLES}</style>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#00ff88", fontSize: "0.85rem", letterSpacing: "0.1em" }}>[ RAMWISE PREDICTION ENGINE ]</span>
          <span style={{ animation: "chainPulse 1s infinite", color: "#00ff88" }}>|</span>
        </div>
        <span style={{ color: "#00ff88", fontSize: "0.7rem", fontFamily: "'JetBrains Mono', monospace" }}>
          TX: {totalCount}
        </span>
      </div>

      <div className="prediction-feed-scroll">
        {feed.map((entry, i) => (
          <div
            key={i}
            className={i === 0 ? "feed-entry-new feed-entry-glow" : ""}
            style={{
              borderLeft: `3px solid ${entry.isSeed ? "#4caf50" : "#00bcd4"}`,
              marginBottom: 10,
              paddingLeft: 12,
              opacity: Math.max(0.15, 1 - i * 0.06),
              background: i === 0 ? "rgba(0,255,136,0.03)" : "transparent",
              borderRadius: 4,
              padding: "8px 12px",
              transition: "opacity 0.3s ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ color: "#555", fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>{entry.timestamp}</span>
              <span
                className={entry.isSeed ? "seed-glow" : "chain-glow"}
                style={{
                  background: entry.isSeed ? "#1b3a1b" : "#0a2a2a",
                  border: `1px solid ${entry.isSeed ? "#4caf5066" : "#00bcd466"}`,
                  color: entry.isSeed ? "#4caf50" : "#00bcd4",
                  padding: "1px 8px",
                  borderRadius: 8,
                  fontSize: 10,
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                {entry.isSeed ? "\uD83C\uDF31 seed" : <span className="chain-icon-pulse">{"\u26D3"} chain</span>}
              </span>
            </div>

            <div style={{ marginBottom: 6, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
              {entry.input.map((app, j) => (
                <span key={j} style={{ display: "inline-flex", alignItems: "center" }}>
                  <span style={{
                    background: "#1a2a3a",
                    border: "1px solid #334",
                    borderRadius: 12,
                    padding: "2px 8px",
                    color: "#ccc",
                    fontSize: 11,
                  }}>{app}</span>
                  {j < entry.input.length - 1 && (
                    <span style={{ color: "#00bcd4", margin: "0 3px", fontSize: 14, fontWeight: "bold", textShadow: "0 0 6px rgba(0,188,212,0.5)" }}>{"\u203A"}</span>
                  )}
                </span>
              ))}
            </div>

            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
              {entry.predicted.map((app, j) => (
                <span
                  key={j}
                  className={j === 0 ? "shimmer-top-badge" : ""}
                  style={{
                    background: j === 0 ? undefined : "#1a1a2e",
                    border: j === 0 ? "1px solid #4caf5066" : "1px solid #222",
                    color: j === 0 ? "#fff" : "#666",
                    padding: "2px 8px",
                    borderRadius: 12,
                    fontSize: 10,
                    fontWeight: j === 0 ? 600 : 400,
                  }}
                >
                  {app} {(entry.confidence[j] * 100).toFixed(1)}%
                </span>
              ))}
            </div>

            <span style={{
              fontSize: 9,
              color: entry.method === "transformer" ? "#4caf50" : "#ff9800",
              background: entry.method === "transformer" ? "#0a1a0a" : "#1a1000",
              border: `1px solid ${entry.method === "transformer" ? "#4caf5033" : "#ff980033"}`,
              padding: "1px 6px",
              borderRadius: 4,
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              [ {entry.method} ]
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
