#!/usr/bin/env bash
# Fetch OFL-licensed Arabic fonts from the google/fonts repository.
set -u
dir="$(cd "$(dirname "$0")/.." && pwd)/backend/app/fonts"
mkdir -p "$dir"
base="https://raw.githubusercontent.com/google/fonts/main/ofl"
declare -A fonts=(
  ["Amiri-Regular.ttf"]="$base/amiri/Amiri-Regular.ttf"
  ["Amiri-Bold.ttf"]="$base/amiri/Amiri-Bold.ttf"
  ["ArefRuqaa-Regular.ttf"]="$base/arefruqaa/ArefRuqaa-Regular.ttf"
  ["ReemKufi.ttf"]="$base/reemkufi/ReemKufi%5Bwght%5D.ttf"
  ["ScheherazadeNew-Regular.ttf"]="$base/scheherazadenew/ScheherazadeNew-Regular.ttf"
  ["Katibeh-Regular.ttf"]="$base/katibeh/Katibeh-Regular.ttf"
  ["Rakkas-Regular.ttf"]="$base/rakkas/Rakkas-Regular.ttf"
)
for name in "${!fonts[@]}"; do
  url="${fonts[$name]}"
  dest="$dir/$name"
  if [ -s "$dest" ]; then echo "skip $name"; continue; fi
  echo "downloading $name"
  curl -fsSL --retry 2 -o "$dest" "$url" || { echo "FAILED $name"; rm -f "$dest"; }
done
# Fallback alias so the default style always resolves even if other files fail.
[ -s "$dir/Amiri-Regular.ttf" ] && cp -f "$dir/Amiri-Regular.ttf" "$dir/NotoNaskhArabic.ttf" 2>/dev/null || true
echo "done"
