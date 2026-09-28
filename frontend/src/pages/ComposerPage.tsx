import { useCallback, useEffect, useRef, useState } from "react";
import { api, type CompositionDoc, type Meta, type PatternSpec } from "../lib/api";
import type { Issue, ValidationReport } from "../lib/api";

const DEFAULT_PATTERN: PatternSpec = {
  style: "khatam8",
  seed: 7,
  tile: 160,
  cols: 8,
  rows: 10,
  palette: "sand",
  line_width: 2,
};

type Spec = {
  text: string;
  style: string;
  font_size: number;
  text_fill: string;
  background: string;
  width: number;
  height: number;
  pattern: PatternSpec | null;
  pattern_opacity: number;
  text_position: string;
};

const EMPTY: Spec = {
  text: "العلم نور والجهل ظلام",
  style: "naskh",
  font_size: 150,
  text_fill: "#1c1c1c",
  background: "#f7f3e8",
  width: 1200,
  height: 1600,
  pattern: { ...DEFAULT_PATTERN },
  pattern_opacity: 0.12,
  text_position: "center",
};

export default function ComposerPage({ meta }: { meta: Meta | null }) {
  const [spec, setSpec] = useState<Spec>(EMPTY);
  const [svg, setSvg] = useState<string>("");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState<CompositionDoc | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const debounce = useRef<number | undefined>(undefined);

  const set = <K extends keyof Spec>(k: K, v: Spec[K]) =>
    setSpec((s) => ({ ...s, [k]: v }));

  const setPattern = (patch: Partial<PatternSpec>) =>
    setSpec((s) => ({
      ...s,
      pattern: s.pattern ? { ...s.pattern, ...patch } : s.pattern,
    }));

  const preview = useCallback(async (s: Spec) => {
    setBusy(true);
    setErr(null);
    try {
      const r = await api.preview(s as never);
      setSvg(r.svg);
      setIssues(r.issues);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  // Debounced live preview.
  useEffect(() => {
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => preview(spec), 350);
    return () => window.clearTimeout(debounce.current);
  }, [spec, preview]);

  const save = async () => {
    setBusy(true);
    try {
      const doc = saved
        ? await api.updateComposition(saved.id, spec as never)
        : await api.createComposition(spec as never);
      setSaved(doc);
      setValidation(null);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const validateNow = async () => {
    if (!saved) {
      setErr("Save the composition first.");
      return;
    }
    setBusy(true);
    try {
      setValidation(await api.validate(saved.id));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!saved) {
      setErr("Save the composition first.");
      return;
    }
    setBusy(true);
    try {
      setSaved(await api.submit(saved.id));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const newDraft = () => {
    setSaved(null);
    setValidation(null);
    setSpec({ ...EMPTY, text: "العلم نور والجهل ظلام" });
  };

  return (
    <div className="composer">
      <section className="panel controls">
        <label>Arabic text</label>
        <textarea
          dir="rtl"
          value={spec.text}
          rows={3}
          onChange={(e) => set("text", e.target.value)}
          placeholder="اكتب هنا..."
        />

        <label>Calligraphy style</label>
        <select value={spec.style} onChange={(e) => set("style", e.target.value)}>
          {(meta?.styles ?? []).map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>

        <div className="row">
          <div className="field">
            <label>Font size {spec.font_size}</label>
            <input type="range" min={40} max={360} value={spec.font_size}
                   onChange={(e) => set("font_size", +e.target.value)} />
          </div>
          <div className="field">
            <label>Opacity {spec.pattern_opacity.toFixed(2)}</label>
            <input type="range" min={0} max={1} step={0.02} value={spec.pattern_opacity}
                   onChange={(e) => set("pattern_opacity", +e.target.value)} />
          </div>
        </div>

        <div className="row">
          <div className="field">
            <label>Text color</label>
            <input type="color" value={spec.text_fill}
                   onChange={(e) => set("text_fill", e.target.value)} />
          </div>
          <div className="field">
            <label>Background</label>
            <input type="color" value={spec.background}
                   onChange={(e) => set("background", e.target.value)} />
          </div>
          <div className="field">
            <label>Position</label>
            <select value={spec.text_position}
                    onChange={(e) => set("text_position", e.target.value)}>
              <option value="top">Top</option>
              <option value="center">Center</option>
              <option value="bottom">Bottom</option>
            </select>
          </div>
        </div>

        <fieldset>
          <legend>Geometric pattern</legend>
          <div className="row">
            <div className="field">
              <label>Style</label>
              <select
                value={spec.pattern?.style ?? "none"}
                onChange={(e) =>
                  setPattern({ style: e.target.value === "none" ? "khatam8" : e.target.value })
                }
              >
                {(meta?.pattern_styles ?? []).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Palette</label>
              <select value={spec.pattern?.palette ?? "sand"}
                      onChange={(e) => setPattern({ palette: e.target.value })}>
                {Object.keys(meta?.palettes ?? { sand: [] }).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="row">
            <div className="field">
              <label>Tile {spec.pattern?.tile ?? 160}px</label>
              <input type="range" min={60} max={400} value={spec.pattern?.tile ?? 160}
                     onChange={(e) => setPattern({ tile: +e.target.value })} />
            </div>
            <div className="field">
              <label>Seed {spec.pattern?.seed ?? 7}</label>
              <button className="btn ghost" onClick={() => setPattern({ seed: Math.floor(Math.random() * 9999) })}>
                🎲 Reroll
              </button>
            </div>
          </div>
          <button className="btn ghost" onClick={() => setSpec((s) => ({ ...s, pattern: s.pattern ? null : { ...DEFAULT_PATTERN } }))}>
            {spec.pattern ? "Disable pattern" : "Enable pattern"}
          </button>
        </fieldset>

        <div className="actions">
          <button className="btn" onClick={save} disabled={busy}>
            {saved ? "Save changes" : "Save draft"}
          </button>
          <button className="btn" onClick={validateNow} disabled={busy || !saved}>
            Validate
          </button>
          <button className="btn primary" onClick={submit} disabled={busy || !saved || saved?.status !== "draft"}>
            Submit for review
          </button>
          <button className="btn ghost" onClick={newDraft}>New</button>
        </div>
      </section>

      <section className="panel preview">
        <div className="preview-frame" dir="rtl">
          {svg ? (
            <div className="svg-holder" dangerouslySetInnerHTML={{ __html: svg }} />
          ) : (
            <div className="placeholder">{busy ? "Rendering…" : "Type Arabic text to preview"}</div>
          )}
        </div>
        {issues.length > 0 && (
          <ul className="issues">
            {issues.map((i, ix) => (
              <li key={ix} className={`issue ${i.severity}`}>{i.message}</li>
            ))}
          </ul>
        )}
        {validation && (
          <div className={`validation ${validation.passed ? "pass" : "fail"}`}>
            <strong>{validation.passed ? "Validation passed" : "Validation failed"}</strong>
            {validation.ocr_used && (
              <span> · OCR similarity: {(validation.similarity * 100).toFixed(1)}%</span>
            )}
            {!validation.ocr_used && (
              <span> · structural checks only (OCR not installed server-side)</span>
            )}
            <ul>
              {validation.issues.map((i, ix) => (
                <li key={ix} className={`issue ${i.severity}`}>{i.message}</li>
              ))}
            </ul>
          </div>
        )}
        {saved && (
          <div className="meta-line">
            <span>#{saved.id}</span>
            <span className={`status ${saved.status}`}>{saved.status.replace("_", " ")}</span>
            {saved.status === "approved" && (
              <>
                <a className="btn ghost" href={api.exportPng(saved.id, 2)}>PNG ×2</a>
                <a className="btn ghost" href={api.exportSvg(saved.id)}>SVG</a>
              </>
            )}
          </div>
        )}
        {err && <div className="banner error">{err}</div>}
      </section>
    </div>
  );
}
