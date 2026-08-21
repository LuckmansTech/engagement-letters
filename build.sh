#!/bin/sh
# NODE_ENV is exported as "production" in this shell, which makes npm skip
# devDependencies. Unset it locally so the build tools resolve.
set -e
cd "$(dirname "$0")"
unset NODE_ENV
python3 restyle.py
./node_modules/.bin/tailwindcss -c tailwind.config.js -i src/tailwind.src.css -o docs/tailwind.css --minify
./node_modules/.bin/esbuild src/main.jsx --bundle --minify --loader:.jsx=jsx \
  --jsx=automatic --define:process.env.NODE_ENV='"production"' --outfile=docs/app.js
ls -la docs
