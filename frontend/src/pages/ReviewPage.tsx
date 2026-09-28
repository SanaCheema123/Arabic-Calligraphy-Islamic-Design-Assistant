import { useCallback, useEffect, useState } from "react";
import { api, type CompositionDoc } from "../lib/api";

export default function ReviewPage() {
  const [items, setItems] = useState<CompositionDoc[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [reviewer, setReviewer] = useState("lead-reviewer");

  const refresh = useCallback(async () => {
    try {
      const r = await api.reviewQueue();
      setItems(r.items);
    } catch (e) {
      setErr(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const act = async (id: string, decision: "approved" | "rejected" | "changes_requested") => {
    setBusy(id);
    setErr(null);
    try {
      await api.review(id, decision, reviewer, notes[id] ?? "");
      await refresh();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Human review queue</h2>
        <div className="row">
          <label className="inline">Reviewer</label>
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
          <button className="btn ghost" onClick={refresh}>Refresh</button>
        </div>
      </div>
      {err && <div className="banner error">{err}</div>}
      {items.length === 0 && <div className="placeholder">Queue is empty — nothing awaiting review.</div>}
      <div className="grid">
        {items.map((d) => (
          <article key={d.id} className="card">
            <div className="card-svg" dir="rtl">
              <img src={`/api/compositions/${d.id}/svg`} alt={d.params.text} />
            </div>
            <div className="card-body">
              <div className="card-title" dir="rtl">{d.params.text}</div>
              <div className="meta-line">
                <span>#{d.id}</span>
                <span>{d.params.style}</span>
                <span>{new Date(d.updated_at).toLocaleString()}</span>
              </div>
              <textarea
                placeholder="Review notes (optional)"
                rows={2}
                value={notes[d.id] ?? ""}
                onChange={(e) => setNotes((n) => ({ ...n, [d.id]: e.target.value }))}
              />
              <div className="actions">
                <button className="btn primary" disabled={busy === d.id}
                        onClick={() => act(d.id, "approved")}>Approve</button>
                <button className="btn warn" disabled={busy === d.id}
                        onClick={() => act(d.id, "changes_requested")}>Changes</button>
                <button className="btn danger" disabled={busy === d.id}
                        onClick={() => act(d.id, "rejected")}>Reject</button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
