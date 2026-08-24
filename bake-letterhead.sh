#!/bin/sh
# Publish the firm's Word letterhead so every user's letters merge onto it,
# with nobody uploading anything.
#
#   ./bake-letterhead.sh ~/Downloads/blank-letterhead.docx
#   ./build.sh
#
# The file is copied to docs/letterhead.docx and fetched by the app at startup.
# It is served alongside the bundle rather than embedded in it: base64 would add
# a third to its size and force a re-download on every app update.
# Commit docs/letterhead.docx and letterhead.json: together they ARE the
# published letterhead. To change it, run this again and rebuild.
set -e
cd "$(dirname "$0")"
[ -n "$1" ] || { echo "usage: ./bake-letterhead.sh <letterhead.dotx|.docx>"; exit 1; }
[ -f "$1" ] || { echo "no such file: $1"; exit 1; }
case "$1" in *.dotx|*.docx) ;; *) echo "expected a .dotx or .docx"; exit 1;; esac
python3 - "$1" << 'PY'
import io, json, os, shutil, sys, zipfile
p = sys.argv[1]
if not zipfile.is_zipfile(p):
    sys.exit("that file is not a valid Word document (not a zip container)")
names = zipfile.ZipFile(p).namelist()
if "word/document.xml" not in names:
    sys.exit("no word/document.xml inside; is this really a Word file?")
os.makedirs("docs", exist_ok=True)
shutil.copyfile(p, "docs/letterhead.docx")
io.open("letterhead.json", "w", encoding="utf-8").write(
    json.dumps({"name": os.path.basename(p)}))
hdrs = [n for n in names if n.startswith("word/header")]
print("  published %s  (%d KB, %d headers, %d images)"
      % (os.path.basename(p), os.path.getsize(p)//1024, len(hdrs),
         len([n for n in names if n.startswith("word/media/")])))
PY
echo "  now run ./build.sh"
