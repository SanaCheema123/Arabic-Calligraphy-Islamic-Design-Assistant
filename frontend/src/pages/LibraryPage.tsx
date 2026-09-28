import { useCallback, useEffect, useState } from "react";
import { api, type CompositionDoc } from "../lib/api";

export default function LibraryPage() {
  const [items, setItems] = useState<CompositionDoc[]>([]);
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [err, setErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await api.listCompositions(status);
      setItems(r.items);
    } catch (e) {
      setErr(String(e));
    }
  }, [status]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const del = async (id: string) => {
    if (!confirm(`Delete composition ${id}?`)) return;
    try {
      await api.deleteComposition(id);
      await refresh();
    } catch (e) {
      setErr(String(e));
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Library</h2>
        <div className="row">
          <select value={status ?? ""} onChange={(e) => setStatus(e.target.value || undefined)}>
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="pending_review">Pending review</option>
            <option value="changes_requested">Changes requested</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button className="btn ghost" onClick={refresh}>Refresh</button>
        </div>
      </div>
      {err && <div className="banner error">{err}</div>}
      {items.length === 0 && <div className="placeholder">No compositions yet — create one in the Composer.</div>}
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
                <span className={`status ${d.status}`}>{d.status.replace("_", " ")}</span>
              </div>
              {d.review && (
                <div className="review-note">
                  {d.review.decision} by {d.review.reviewer}
                  {d.review.notes ? ` — “${d.review.notes}”` : ""}
                </div>
              )}
              <div className="actions">
                {d.status === "approved" && (
                  <>
                    <a className="btn ghost" href={api.exportPng(d.id, 2)}>PNG ×2</a>
                    <a className="btn ghost" href={api.exportSvg(d.id)}>SVG</a>
                  </>
                )}
                {d.status === "changes_requested" && d.review?.notes && (
                  <span className="review-note">⚠ {d.review.notes}</span>
                )}
                <button className="btn danger ghost" onClick={() => del(d.id)}>Delete</button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
