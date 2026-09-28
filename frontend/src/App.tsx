import { useEffect, useState } from "react";
import { api, type Meta } from "./lib/api";
import ComposerPage from "./pages/ComposerPage";
import ReviewPage from "./pages/ReviewPage";
import LibraryPage from "./pages/LibraryPage";

type Tab = "composer" | "library" | "review";

export default function App() {
  const [tab, setTab] = useState<Tab>("composer");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">❋</span>
          <span className="brand-name">Mishkat</span>
          <span className="brand-sub">Arabic Calligraphy Studio</span>
        </div>
        <nav>
          {(["composer", "library", "review"] as Tab[]).map((t) => (
            <button
              key={t}
              className={`tab ${tab === t ? "active" : ""}`}
              onClick={() => setTab(t)}
            >
              {t === "composer" ? "Composer" : t === "library" ? "Library" : "Review"}
            </button>
          ))}
        </nav>
        {meta && <div className="ocr-badge">OCR {meta.ocr_available ? "on" : "off"}</div>}
      </header>
      {error && <div className="banner error">API unreachable: {error}</div>}
      <main>
        {tab === "composer" && <ComposerPage meta={meta} />}
        {tab === "library" && <LibraryPage />}
        {tab === "review" && <ReviewPage />}
      </main>
    </div>
  );
}
