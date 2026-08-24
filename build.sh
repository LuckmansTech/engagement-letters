#!/bin/sh
# Build the engagement letter tool.
#
#   ./build.sh            PUBLIC build  -> docs/          Letter tab only.
#                                          The clause and people editors are
#                                          not compiled in, so there is nothing
#                                          to unhide.
#   ./build.sh --admin    ADMIN build   -> admin-build/   All three tabs.
#                                          Run locally only. Gitignored on
#                                          purpose: docs/ is served publicly by
#                                          GitHub Pages, so anything inside it
#                                          is world-readable.
#
# Publishing a wording change: run --admin, edit in Templates, Export library,
# paste the JSON over SEED_LIBRARY in src/upstream/, run ./build.sh, upload docs/.
#
# NODE_ENV is exported as "production" in this shell, which makes npm skip
# devDependencies. Unset it locally so the build tools resolve.
set -e
cd "$(dirname "$0")"
unset NODE_ENV

if [ "$1" = "--admin" ]; then
  export RESTYLE_ADMIN=1
  OUTDIR=admin-build
else
  OUTDIR=docs
fi
mkdir -p "$OUTDIR"
[ -f "$OUTDIR/index.html" ] || cp docs/index.html "$OUTDIR/index.html"

python3 restyle.py
./node_modules/.bin/tailwindcss -c tailwind.config.js -i src/tailwind.src.css -o "$OUTDIR/tailwind.css" --minify
./node_modules/.bin/esbuild src/main.jsx --bundle --minify --loader:.jsx=jsx \
  --jsx=automatic --define:process.env.NODE_ENV='"production"' --outfile="$OUTDIR/app.js"
ls -la "$OUTDIR"
