import React, { useState } from "react";
import { locateFromSnapshot } from "../services/snapshotService";
import type { SnapshotLocateResponse } from "../types";

type Props = {
  onResult: (result: SnapshotLocateResponse) => void;
};

const SnapshotLocate: React.FC<Props> = ({ onResult }) => {
  const [endpoint, setEndpoint] = useState("");
  const [snapshotId, setSnapshotId] = useState<string>("");
  const [registeredOnly, setRegisteredOnly] = useState(true);
  const [maxCells, setMaxCells] = useState(12);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SnapshotLocateResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const id = Number(snapshotId);
    if (!endpoint.trim()) {
      setError("Endpoint is required");
      return;
    }
    if (!Number.isFinite(id) || id <= 0) {
      setError("Snapshot ID must be a positive number");
      return;
    }

    setIsLoading(true);
    try {
      const result = await locateFromSnapshot({
        endpoint: endpoint.trim(),
        snapshot_id: id,
        registered_only: registeredOnly,
        max_cells: maxCells,
        include_anchors: true,
        anchors_limit: 25,
      });
      setResult(result);
      onResult(result);
    } catch (err: any) {
      setError(err.message || "Failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.panel}>
      <h2 style={styles.title}>Snapshot Locate</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          Snapshot Endpoint
          <input
            style={styles.input}
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            placeholder="https://api.example.com/snapshots"
          />
        </label>
        <label style={styles.label}>
          Snapshot ID
          <input
            style={styles.input}
            value={snapshotId}
            onChange={(e) => setSnapshotId(e.target.value)}
            placeholder="33299"
            inputMode="numeric"
          />
        </label>
        <label style={styles.checkbox}>
          <input
            type="checkbox"
            checked={registeredOnly}
            onChange={(e) => setRegisteredOnly(e.target.checked)}
          />
          Registered only
        </label>
        <label style={styles.label}>
          Max cells
          <input
            type="number"
            min={1}
            max={50}
            style={styles.input}
            value={maxCells}
            onChange={(e) => setMaxCells(Number(e.target.value))}
          />
        </label>
        <button type="submit" style={styles.button} disabled={isLoading}>
          {isLoading ? "Locating..." : "Locate"}
        </button>
      </form>

      {error && <div style={styles.error}>{error}</div>}
      <div style={styles.hint}>
        Note: backend enforces allowlist via <code>SNAPSHOT_ALLOWED_HOSTS</code>.
      </div>

      {result?.snapshot_cells && (
        <details style={styles.details}>
          <summary style={styles.summary}>
            Towers (from snapshot): {result.snapshot_cells.length}
          </summary>
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>#</th>
                  <th style={styles.th}>Type</th>
                  <th style={styles.th}>MCC/MNC</th>
                  <th style={styles.th}>LAC/TAC</th>
                  <th style={styles.th}>CID</th>
                  <th style={styles.th}>PCI</th>
                  <th style={styles.th}>EARFCN</th>
                  <th style={styles.th}>RSRP/DBM</th>
                  <th style={styles.th}>RSRQ</th>
                  <th style={styles.th}>Reg</th>
                  <th style={styles.th}>In DB</th>
                  <th style={styles.th}>Tower Lat/Lon</th>
                  <th style={styles.th}>Source</th>
                </tr>
              </thead>
              <tbody>
                {result.snapshot_cells.map((c, idx) => (
                  <tr key={idx}>
                    <td style={styles.td}>{idx + 1}</td>
                    <td style={styles.td}>{c.type ?? "—"}</td>
                    <td style={styles.td}>
                      {c.mcc ?? "—"}/{c.mnc ?? "—"}
                    </td>
                    <td style={styles.td}>{c.lac ?? "—"}</td>
                    <td style={styles.td}>{c.cell_id ?? "—"}</td>
                    <td style={styles.td}>{c.pci ?? "—"}</td>
                    <td style={styles.td}>{c.earfcn ?? "—"}</td>
                    <td style={styles.td}>{c.rsrp ?? c.dbm ?? "—"}</td>
                    <td style={styles.td}>{c.rsrq ?? "—"}</td>
                    <td style={styles.td}>{c.registered == null ? "—" : c.registered ? "Y" : "N"}</td>
                    <td style={styles.td}>
                      <span
                        style={{
                          ...styles.badge,
                          background: c.tower_found ? "#22c55e" : "#ef4444",
                        }}
                      >
                        {c.tower_found ? "YES" : "NO"}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {c.tower_found && c.tower_lat != null && c.tower_lon != null
                        ? `${Number(c.tower_lat).toFixed(7)},${Number(c.tower_lon).toFixed(7)}`
                        : "—"}
                    </td>
                    <td style={styles.td}>{c.tower_source ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  panel: {
    background: "linear-gradient(135deg, #0b1221, #111827)",
    color: "#e5e7eb",
    padding: 16,
    borderRadius: 16,
    boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
    maxWidth: 900,
    margin: "20px auto",
  },
  title: { marginBottom: 12, fontWeight: 800 },
  form: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))",
    gap: 12,
    alignItems: "end",
  },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 14 },
  input: {
    background: "#0f172a",
    color: "#e5e7eb",
    border: "1px solid #334155",
    borderRadius: 10,
    padding: 10,
  },
  checkbox: { display: "flex", alignItems: "center", gap: 8, marginTop: 8 },
  button: {
    background: "#a855f7",
    color: "#0b1221",
    border: "none",
    borderRadius: 12,
    padding: "10px 14px",
    cursor: "pointer",
    fontWeight: 800,
  },
  error: { marginTop: 12, color: "#fca5a5" },
  hint: { marginTop: 10, color: "#93c5fd", fontSize: 12 },
  details: {
    marginTop: 14,
    background: "#0b1221",
    borderRadius: 12,
    padding: 10,
    border: "1px solid #1f2937",
  },
  summary: {
    cursor: "pointer",
    fontWeight: 700,
    color: "#e5e7eb",
    listStyle: "none",
  },
  tableWrap: { marginTop: 10, overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 12 },
  th: {
    textAlign: "left",
    padding: "6px 8px",
    borderBottom: "1px solid #1f2937",
    color: "#93c5fd",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "6px 8px",
    borderBottom: "1px solid #111827",
    color: "#e5e7eb",
    whiteSpace: "nowrap",
  },
  badge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 999,
    fontWeight: 800,
    color: "#0b1221",
  },
};

export default SnapshotLocate;
