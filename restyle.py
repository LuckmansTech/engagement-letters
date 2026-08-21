#!/usr/bin/env python3
"""
Apply the PracticeOS design layer to whatever version of the engagement letter
lands in src/upstream/. Run it again after every drop; never hand-edit the
generated file.

    src/upstream/engagement-letter.jsx   pristine, straight from the tool author
    restyle.py                           this file: our layer
    src/engagement-letter.jsx            GENERATED - do not edit

Three principles:

  1. Nothing here touches the engine. The clause library, assemble(), toHtml(),
     docxBody() and both .docx writers are never matched by any rule below.
  2. Anchors are structural, not positional. Rules match a definition or an
     element, so upstream can change wording, add clauses or move code without
     breaking us.
  3. It fails loudly. If an anchor is gone or a handler was renamed, the script
     stops and says which one, rather than emitting a half-styled build.
"""
import io, re, sys

SRC = "src/upstream/engagement-letter.jsx"
OUT = "src/engagement-letter.jsx"
applied, warnings = [], []

def die(msg):
    print("\n  RESTYLE FAILED\n  " + msg + "\n")
    sys.exit(1)

s = io.open(SRC, encoding="utf-8").read()
ENGINE_END = s.find("const C = {")
if ENGINE_END < 0:
    die("cannot find the token block; the file layout has changed fundamentally")

def sub(pattern, repl, label, flags=0, expect=1):
    """Replace by regex. repl is a plain string, inserted literally."""
    global s
    n = len(re.findall(pattern, s, flags))
    if n != expect:
        die("expected %d match(es) for '%s', found %d" % (expect, label, n))
    s = re.sub(pattern, lambda m: repl, s, count=expect, flags=flags)
    applied.append(label)

def subf(pattern, fn, label, flags=0, expect=1):
    """Replace by regex, repl is a function of the match (keeps groups)."""
    global s
    n = len(re.findall(pattern, s, flags))
    if n != expect:
        die("expected %d match(es) for '%s', found %d" % (expect, label, n))
    s = re.sub(pattern, fn, s, count=expect, flags=flags)
    applied.append(label)

def need(*syms):
    missing = [x for x in syms if x not in s]
    if missing:
        die("upstream no longer provides: " + ", ".join(missing) +
            "\n  The shell markup calls these. Update restyle.py to match.")

# The shell we inject calls all of these. Check before writing anything.
need("doWord", "doPdf", "converting", "exportLib", "importLib", "loadTpl",
     "restoring", "setTab", "model.ref", "screenHtml", "setPartners", "setStaff")
if "const [stale" in s and "setStale(" not in s:
    warnings.append("`stale` is declared upstream but never set, so the preview "
                    "freshness pill is omitted. It would always read 'up to date'.")

# ---------------------------------------------------------------- 1. tokens
sub(r'^const C = \{ ink:.*\};$', '''/* PracticeOS design tokens. The seven names above the divider are the ones the
   upstream render already uses; only their values change. The names below are
   added by this layer. */
const C = {
  ink: "#0C1A2E", shell: "#EEF3FB", accent: "#1550AA", soft: "#DDE8FF",
  muted: "#7A96B8", rule: "#DDE8F5", ochre: "#DC2626",
  /* ------------------------------------------------------------------ */
  accH: "#0E3D88", accS: "#EEF3FF", surf: "#FFFFFF", surf2: "#F5F8FD",
  surf3: "#EAF0FA", rule2: "#C6D8EE", tx2: "#3A5378", txd: "#B4C8DE",
  ok: "#059669", okBg: "#D1FAE5", wa: "#D97706", waBg: "#FEF3C7",
  er: "#DC2626", erBg: "#FEE2E2",
};''', "colour tokens", re.M)

sub(r'^const UI = .*;$',
    'const UI = "system-ui,-apple-system,\'Segoe UI\',Helvetica,Arial,sans-serif";',
    "UI font stack (matches mornng; no webfont)", re.M)

# ------------------------------------------------------- 2. control shapes
sub(r'^const INP = \{.*\};$',
    'const INP = { fontFamily: UI, fontSize: 12.5, lineHeight: 1.4, color: C.ink, '
    'background: C.surf, border: `1px solid ${C.rule}`, borderRadius: 8, '
    'padding: "6px 9px", minHeight: 32, width: "100%", minWidth: 0, boxSizing: "border-box" };',
    "inputs to 32px on an 8px radius", re.M)

sub(r'^const Lab = \(\{ children \}\).*$',
    'const Lab = ({ children }) => <span style={{ display: "block", fontFamily: UI, '
    'fontSize: 10, textTransform: "uppercase", letterSpacing: ".06em", color: C.muted, '
    'fontWeight: 700, marginBottom: 4 }}>{children}</span>;',
    "field labels", re.M)

sub(r'^const H = \(\{ children \}\).*$',
    'const H = ({ children }) => <div style={{ fontFamily: UI, fontSize: 10, fontWeight: 700, '
    'letterSpacing: ".1em", textTransform: "uppercase", color: C.muted, '
    'borderBottom: `1px solid ${C.rule}`, paddingBottom: 7, margin: "18px 0 10px" }}>{children}</div>;',
    "section captions", re.M)

sub(r'^const R = \(\{ c, children \}\).*$',
    'const R = ({ c, children }) => <div style={{ display: "grid", gridTemplateColumns: c, '
    'gap: 10, marginBottom: 11 }}>{children}</div>;',
    "form row rhythm", re.M)

sub(r'^  const ASIDE = \{.*\};$',
    '  const ASIDE = { background: C.surf, border: `1px solid ${C.rule}`, borderRadius: 12 };',
    "form panel becomes a card", re.M)


# ------------------------------------------------------ 3. injected styles
sub(r'<style>\{`[\s\S]*?`\}</style>', """<style>{`
        input:focus,select:focus,textarea:focus{border-color:${C.accent}!important;outline:none}
        button{cursor:pointer}
        .pOsTab{height:100%;padding:0 14px;font-weight:600;color:${C.muted};
          border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}
        .pOsTab:hover{color:${C.tx2}}
        .pOsTab[data-on="1"]{color:${C.accent};font-weight:700;border-bottom-color:${C.accent}}
        .pOsBtn{height:32px;padding:0 14px;border-radius:8px;font-size:12.5px;font-weight:600;
          display:inline-flex;align-items:center;gap:6px;border:1px solid ${C.rule};
          background:${C.surf};color:${C.ink}}
        .pOsBtn:hover{background:${C.surf2}}
        .pOsBtn.pri{background:${C.accent};border-color:${C.accent};color:#fff;font-weight:700}
        .pOsBtn.pri:hover{background:${C.accH}}
        .pOsBtn:disabled{opacity:.55;cursor:default}
        /* H sets its margin inline, so this needs the override */
        aside.pane > div:first-child{margin-top:4px!important}
        ::-webkit-scrollbar{width:9px;height:9px}
        ::-webkit-scrollbar-thumb{background:${C.rule2};border-radius:999px}
        ::-webkit-scrollbar-track{background:transparent}
        @media (min-width:768px){ aside.pane{width:420px;flex:0 0 420px} }
        @media (min-width:1400px){ aside.pane{width:460px;flex:0 0 460px} }
        @media (min-width:1700px){ aside.pane{width:500px;flex:0 0 500px} }`}</style>""",
    "injected stylesheet, panel tiers 420/460/500")

# ------------------------------------------------------------- 4. the shell
# Replaces the whole <header> element structurally, so upstream can rearrange
# its contents freely. Everything this markup calls was checked by need().
# Everything lives in one bar, matching the placement of the original: title
# and firm, tabs, our ref, letterhead state, then the actions right-aligned.
# The markup is held in shell_block.txt so the JSX is not buried in a string.
sub(r'<header className="flex flex-wrap[\s\S]*?</header>',
    io.open("shell_block.txt", encoding="utf-8").read().rstrip("\n"),
    "single top bar: title, tabs, ref, letterhead, actions")


# ------------------------------------------------------------ 5. the panes
sub(r'<div className=\{"flex flex-col " \+ "md:flex-row"\}>\s*<aside className="pane[^"]*" style=\{ASIDE\} >',
    '<div className="flex flex-col gap-4 md:flex-row"\n'
    '          style={{ maxWidth: 1600, margin: "0 auto", padding: "14px 20px 28px" }}>\n'
    '          <aside className="pane w-full shrink-0 px-4 pb-5 md:sticky md:top-[56px] '
    'md:max-h-[calc(100vh-72px)] md:overflow-y-auto" style={ASIDE} >',
    "letter pane: container 1600, panel as a sticky card")

sub(r'<main className="flex-1 p-2 md:p-3 lg:p-5 min-w-0">[\s\S]*?</main>',
    '<main className="flex-1 min-w-0 md:sticky md:top-[56px]" style={{ alignSelf: "flex-start" }}>\n'
    '            <div style={{ background: "#E4ECF8", border: `1px solid ${C.rule}`, borderRadius: 12, padding: 16 }}>\n'
    '              <iframe title="letter" srcDoc={screenHtml} style={{ width: "100%", maxWidth: "210mm", '
    'height: "calc(100vh - 136px)", border: "none", background: "#fff", display: "block", margin: "0 auto", '
    'borderRadius: 2, boxShadow: "0 4px 12px rgba(12,26,46,.08),0 16px 40px rgba(12,26,46,.10)" }} />\n'
    '            </div>\n          </main>',
    "letter on a recessed stage, capped at exactly A4")

sub(r'<div className="flex flex-col lg:flex-row">',
    '<div className="flex flex-col lg:flex-row gap-4" style={{ maxWidth: 1600, margin: "0 auto", padding: "14px 20px 28px" }}>',
    "templates pane container")

sub(r'<aside className="w-full lg:w-72 shrink-0 px-3 py-3 lg:h-\[calc\(100vh-52px\)\][^>]*>',
    '<aside className="w-full lg:w-72 shrink-0 px-3 py-3 lg:max-h-[calc(100vh-72px)] '
    'lg:overflow-y-auto lg:sticky lg:top-[56px]" style={{ background: C.surf, '
    'border: `1px solid ${C.rule}`, borderRadius: 12 }}>',
    "clause list becomes a card")

sub(r'<main className="p-5 lg:p-8 overflow-y-auto" style=\{\{ maxHeight: "calc\(100vh - 52px\)" \}\}>\s*<div className="mx-auto" style=\{\{ maxWidth: 760 \}\}>',
    '<main style={{ maxWidth: 1600, margin: "0 auto", padding: "14px 20px 32px" }}>\n'
    '          <div style={{ maxWidth: 880 }}>',
    "firm pane aligns with the action row")

sub(r'maxHeight: "calc\(100vh - 52px\)"', 'maxHeight: "calc(100vh - 72px)"',
    "scroll height follows the taller head")

# --------------------------------------------------- 6. row ratios for dates
# A date column needs about 183px: 130 of text, 20 padding, 2 border, 4 gap and
# a 27px calendar button. Upstream gives it the smallest share of its row.
subf(r'(<R c=")[^"]*(">\s*<label><Lab>Client name</Lab>)',
     lambda m: m.group(1) + "1fr 1.3fr" + m.group(2),
     "client row: the date takes the larger share")
subf(u'(<R c=")[^"]*(">\\s*<label><Lab>Cap \u00a3</Lab>)',
     lambda m: m.group(1) + "1fr 1fr 2.2fr" + m.group(2),
     "firm row: letter date stays in place, widened")

# --------------------------------------------- 7. upstream bug: the Firm tab
# Written as `letter ? A : B` with no third arm, so Firm falls into the
# Templates branch and renders the clause library above its own panel.
sub(r'\n      \) : \(\n        <div className="flex flex-col lg:flex-row gap-4"',
    '\n      ) : tab === "templates" ? (\n        <div className="flex flex-col lg:flex-row gap-4"',
    "BUGFIX: Firm tab rendered the Templates layout")
sub(r'\n      \)\}\n\n      \{tab === "firm" && \(',
    '\n      ) : null}\n\n      {tab === "firm" && (',
    "BUGFIX: close the third branch")

# ------------------------------------------- 8. firm people: imported, kept
# Held in people_block.txt so the JSX is not buried in a Python string.
sub(r'    r\.readAsArrayBuffer\(file\); \};',
    io.open("people_block.txt", encoding="utf-8").read().rstrip("\n"),
    "firm people import/export, persisted")

# ------------------------------------------- 9. drop the first section header
# "Engagement" captions a single control and repeats what the page already
# says, so the panel opens straight on Client type.
sub(r'\n *<H>Engagement</H>', '', "remove the redundant Engagement caption")

io.open(OUT, "w", encoding="utf-8").write(s)
print("")
print("  RESTYLED  %s" % OUT)
print("  %d rules applied:" % len(applied))
for a in applied: print("    - " + a)
for w in warnings: print("\n  note: " + w)
print("")
