# Mishkat — Arabic Calligraphy & Islamic Design Assistant


https://github.com/user-attachments/assets/1dee6a2f-0a38-4d9f-bb62-4024b7ae0ede


A creative tool that generates **Arabic calligraphy compositions** and **Saudi-inspired
geometric patterns** for posters, packaging, events, and digital media — with
**human review required before any publication-ready export**.

## Features

- **Arabic text input** with correct RTL shaping (arabic-reshaper + python-bidi),
  embedded fonts, and lam-alef ligature support.
- **7 calligraphy styles** built on OFL-licensed fonts: Naskh (Amiri), Ruq'ah (Aref
  Ruqaa), Kufi (Reem Kufi), Thuluth-like (Scheherazade), Diwani-like (Katibeh),
  Decorative (Rakkas), Naskh Bold.
- **Geometric pattern generation**: 5 procedural motifs — 8-fold khatam, 10-fold
  girih rosette, 12-fold star grid, nested squares, interlaced braid — each tileable,
  recolorable, and seed-driven for deterministic variants.
- **Layout & color customization**: font size, text/background colors, position,
  pattern opacity, tile size, palettes (sand, oasis, night, riyad, monochrome).
- **Text-accuracy validation**: structural Unicode checks always run; OCR round-trip
  (Tesseract `ara`) when installed, reporting read-back similarity.
- **Human review workflow**: draft → pending_review → approved/rejected/changes_requested.
  Editing is locked while pending; **export is blocked (HTTP 403) until approved**.
- **High-resolution export**: PNG up to 8× scale (300 DPI) and vector SVG.

## Stack

| Layer     | Tech |
|-----------|------|
| Frontend  | React 18, TypeScript, Vite |
| Backend   | FastAPI, Python 3.10+ |
| Rendering | arabic-reshaper, python-bidi, fontTools, CairoSVG (rasterization) |
| Patterns  | Pure-Python geometry → standalone SVG (deterministic, seed-driven) |
| Validation| Unicode structural checks + Tesseract OCR (`ara`) optional |
| Storage   | JSON files under `backend/data/` (zero-config, easy to swap) |

> **Diffusers / ControlNet**: the pattern engine is deterministic geometry rather
> than diffusion, so it runs offline with zero GPU and the outputs are exactly
> reproducible from `(style, seed, palette)`. The FastAPI layer isolates generation
> behind endpoints, so a diffusion backend can be added later as another
> "pattern style" without touching the frontend.

## Quick start

Prerequisites: **Python 3.10+** and **Node 18+**.

```bash
# 1. Backend
pip install -r mishkat/backend/requirements.txt
bash mishkat/scripts/fetch_fonts.sh        # downloads OFL fonts (~2 MB)
cd mishkat/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Frontend (second terminal)
cd mishkat/frontend
npm install
npm run dev                                 # http://localhost:5173
```

Optional OCR validation:

```bash
# Windows (admin) : choco install tesseract-ocr   then get ara.traineddata
# Ubuntu          : sudo apt install tesseract-ocr tesseract-ocr-ara
```

The header badge shows `OCR on/off`; without it, validation still performs all
structural checks and the app degrades gracefully.

## Tests

```bash
bash mishkat/scripts/e2e_test.sh            # 14-check API workflow test
python mishkat/backend/tests/smoke.py       # offline unit smoke (shaping, render, store)
cd mishkat/frontend && npx tsc --noEmit     # frontend typecheck
```

## API overview

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/health`, `/api/meta` | service + capabilities |
| POST | `/api/render/composition`  | stateless preview SVG |
| POST | `/api/pattern`, `/api/pattern/variants` | pattern SVG / variants |
| POST/GET | `/api/compositions`   | create / list |
| GET/PUT/DELETE | `/api/compositions/{id}` | fetch / edit (locked while pending) / delete |
| GET  | `/api/compositions/{id}/svg` | inline SVG |
| POST | `/api/compositions/{id}/validate` | structural + OCR report |
| POST | `/api/compositions/{id}/submit`   | draft → pending_review |
| GET  | `/api/review/queue` | pending items |
| POST | `/api/compositions/{id}/review` | approve / reject / changes_requested |
| GET/POST | `/api/compositions/{id}/export?scale=n` | PNG (approved only) |
| GET  | `/api/compositions/{id}/export/svg` | vector (approved only) |

Interactive docs: `http://localhost:8000/docs`

## Workflow

1. **Composer** — type Arabic, pick style, tune pattern/colors; live preview
   debounces to `/api/render/composition`.
2. **Save draft** → **Validate** (structural + optional OCR read-back).
3. **Submit for review** — the draft is locked from editing.
4. A human reviewer approves, requests changes (with notes), or rejects in the
   **Review** tab.
5. Only **approved** compositions expose the **PNG ×2 / SVG** export buttons —
   enforced server-side, not just hidden in the UI.

## Adding a calligraphy style

Append a tuple to `STYLES` in `backend/app/rendering/svgtext.py`:
`(font_file, label, fallback_size, line_height, letter_spacing, font_weight)`,
drop the `.ttf` into `backend/app/fonts/`, restart. The frontend picks it up
from `/api/meta` automatically.

## Project layout

```
mishkat/
├── backend/
│   ├── app/
│   │   ├── arabic/        # validation, normalization, bidi shaping
│   │   ├── rendering/     # SVG text, composition, PNG rasterizer
│   │   ├── patterns/      # geometric motif engine
│   │   ├── validation/    # OCR round-trip + structural checks
│   │   ├── fonts/         # OFL .ttf files (downloaded)
│   │   ├── main.py        # FastAPI routes
│   │   ├── store.py       # JSON-file persistence
│   │   └── config.py
│   ├── data/              # compositions/ + exports/ (gitignored-able)
│   └── tests/
├── frontend/              # React + Vite app
└── scripts/               # fetch_fonts.sh, e2e_test.sh
```

## License notes

Fonts are OFL-licensed (SIL Open Font License) and fetched from the
`google/fonts` repository at setup time — see `scripts/fetch_fonts.sh`.
