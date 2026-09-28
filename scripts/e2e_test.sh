#!/usr/bin/env bash
# End-to-end API test: boots uvicorn, exercises the full workflow, shuts down.
set -u
cd "$(cd "$(dirname "$0")/.." && pwd)/backend"

PORT=8123
BASE="http://127.0.0.1:$PORT"
python -m uvicorn app.main:app --host 127.0.0.1 --port $PORT > /tmp/mishkat_e2e.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT

# Wait for health
for i in $(seq 1 30); do
  if curl -sf "$BASE/api/health" > /dev/null 2>&1; then break; fi
  sleep 0.5
done

fail=0
check() { # name, expected_substring, actual
  if echo "$3" | grep -q "$2"; then echo "PASS $1"; else echo "FAIL $1 (wanted '$2' in: ${3:0:200})"; fail=1; fi
}

H=$(curl -sf "$BASE/api/health")
check health '"ok": *true' "$H"

M=$(curl -sf "$BASE/api/meta")
check meta '"styles"' "$M"

P=$(curl -sf -X POST "$BASE/api/pattern" -H 'Content-Type: application/json' \
  -d '{"style":"girih10","seed":11,"cols":3,"rows":3}')
check pattern 'patternUnits' "$P"

V=$(curl -sf -X POST "$BASE/api/pattern/variants?count=3" -H 'Content-Type: application/json' \
  -d '{"style":"star12","seed":5}')
check variants '"variants"' "$V"

R=$(curl -sf -X POST "$BASE/api/render/composition" -H 'Content-Type: application/json' \
  -d '{"text":"العلم نور","style":"naskh","font_size":140,"text_fill":"#111111","background":"#f7f3e8","width":1200,"height":1600,"pattern":{"style":"khatam8","seed":7,"tile":160,"cols":8,"rows":10,"palette":"sand","line_width":2},"pattern_opacity":0.12,"text_position":"center"}')
check preview 'mk-comp-tile' "$R"

C=$(curl -sf -X POST "$BASE/api/compositions" -H 'Content-Type: application/json' \
  -d '{"text":"هيا نرتقي","style":"diwani_like","font_size":150,"text_fill":"#0b3d2e","background":"#f7f3e8","width":1200,"height":1600,"pattern":null,"pattern_opacity":0.1,"text_position":"center"}')
check create '"status": *"draft"' "$C"
CID=$(echo "$C" | sed -n 's/.*"id":"\([a-f0-9]*\)".*/\1/p' | head -1)
echo "composition id: $CID"

VAL=$(curl -sf -X POST "$BASE/api/compositions/$CID/validate")
check validate '"passed"' "$VAL"

S=$(curl -sf -X POST "$BASE/api/compositions/$CID/submit")
check submit '"pending_review"' "$S"

# Editing a pending composition must be blocked (409)
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/api/compositions/$CID" -H 'Content-Type: application/json' \
  -d '{"text":"لا يزال نفسه","style":"naskh","font_size":120,"text_fill":"#111","background":"#f7f3e8","width":1200,"height":1600,"pattern":null,"pattern_opacity":0.1,"text_position":"center"}')
check edit_blocked '^409$' "$CODE"

Q=$(curl -sf "$BASE/api/review/queue")
check queue "$CID" "$Q"

AP=$(curl -sf -X POST "$BASE/api/compositions/$CID/review" -H 'Content-Type: application/json' \
  -d '{"decision":"approved","reviewer":"test-bot","notes":"looks good"}')
check approve '"approved"' "$AP"

# Export PNG + SVG (approved only)
EXP=$(curl -sf -X POST "$BASE/api/compositions/$CID/export?scale=2" -o /tmp/mk_exp.png -w "%{http_code} %{size_download}")
echo "export png: $EXP"
file /tmp/mk_exp.png 2>/dev/null || head -c 8 /tmp/mk_exp.png | od -c | head -1
EXPV=$(curl -sf "$BASE/api/compositions/$CID/export/svg" | head -c 60)
check export_svg '<svg' "$EXPV"

# SVG export must be blocked before approval
C2=$(curl -sf -X POST "$BASE/api/compositions" -H 'Content-Type: application/json' \
  -d '{"text":"تجربة","style":"kufi","font_size":120,"text_fill":"#111","background":"#fff","width":1000,"height":1000,"pattern":null,"pattern_opacity":0.1,"text_position":"center"}')
CID2=$(echo "$C2" | sed -n 's/.*"id":"\([a-f0-9]*\)".*/\1/p' | head -1)
CODE2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/compositions/$CID2/export?scale=1")
check export_blocked '^403$' "$CODE2"

curl -sf -X DELETE "$BASE/api/compositions/$CID2" > /dev/null

if [ "$fail" = "0" ]; then echo "ALL E2E TESTS PASSED"; else echo "E2E FAILURES"; exit 1; fi
