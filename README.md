# Engagement letters

Generates a Luckmans letter of engagement from a clause library, and emits it as
HTML, print/PDF, or a `.docx` merged onto the firm's own Word letterhead.

Destined to become a module inside [Mornng](https://github.com/LuckmansTech/Mornng);
this repo is the standalone build used to test it in the meantime.

## Layout

    src/engagement-letter.jsx   the app. Lines 1-718 are the engine: clause
                                library, vocabulary, assembler, HTML emitter and
                                both .docx writers. Presentation lives below it.
    src/storage.js              IndexedDB shim for the window.storage API that
                                the Claude artifact runtime provides and a plain
                                browser does not.
    src/main.jsx                entry point.
    docs/                       the built site. GitHub Pages serves from here.

## Build

    ./build.sh

Note: this machine exports `NODE_ENV=production` globally, which makes npm skip
devDependencies. `build.sh` unsets it locally; if you install by hand, use
`npm install --include=dev`.

## Design

Chrome follows the PracticeOS design language: accent `#1550AA`, 32px controls
on an 8px radius, 12px cards, underline-only tabs, one primary button per view.
The A4 letter itself is deliberately exempt — it stays Arial 10pt on the firm's
letterhead, because it is the legal deliverable rather than app chrome.

## Firm people

Partners and staff are imported, not hardcoded. The Firm tab takes a JSON file
`{ partners: [...], staff: [...] }` or a CSV with a header row naming the
columns `group, title, name, initials` in any order. Group is `partner` (or
`director`) for the partner list, anything else for staff. Missing initials are
derived from the name. The imported list persists in the browser.

## Working on this after an upstream drop

The tool is authored elsewhere and arrives as a single `engagement-letter.jsx`.
Our design layer is applied by script, not by hand, so a new version does not
mean redoing the design.

    src/upstream/engagement-letter.jsx   drop the new file here, untouched
    restyle.py                           our layer
    src/engagement-letter.jsx            GENERATED - never edit this

So the whole process is:

    cp ~/Downloads/engagement-letter.jsx src/upstream/
    ./build.sh          # runs restyle.py, then tailwind, then esbuild

`restyle.py` matches definitions and elements rather than line numbers, so
upstream can rewrite clause text, add schedules, or rearrange the header
without breaking it. Before it writes anything it checks that every handler the
injected markup calls still exists; if one has been renamed it stops and says
which. If a rule matches the wrong number of times it stops too. A half-styled
build is never produced silently.

It also re-applies two things upstream does not carry: the firm people import,
and a fix for the Firm tab rendering the Templates layout.

The engine - clause library, `plan()`, `assemble()`, `toHtml()` and both `.docx`
writers - is never matched by any rule. Verify after any drop:

    python3 - <<'PY'
    import hashlib, io
    u = io.open("src/upstream/engagement-letter.jsx").read()
    g = io.open("src/engagement-letter.jsx").read()
    n = u[:u.find("const C = {")].count("\n")
    h = lambda t: hashlib.sha256("\n".join(t.split("\n")[:n]).encode()).hexdigest()[:16]
    print("IDENTICAL" if h(u) == h(g) else "DIFFERS")
    PY

`HANDOVER.md` is the tool author's own document and is the authority on the
clause library, the letterhead merge and the outstanding work. Read it before
changing anything in the engine.

## Known, and not ours to fix

- `PDF_ENDPOINT` is empty, so the PDF button downloads the `.docx`. It needs a
  server route running `soffice --headless --convert-to pdf`. See HANDOVER.md 9e.
- `stale` is declared but never set upstream, so the preview freshness
  indicator has no wiring. The restyle script warns about this on every run.
