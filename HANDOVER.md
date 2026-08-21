# Engagement letter generator: handover

Prepared 21-08-2026 for Luckmans Duckett Parker Limited, to continue the work in a fresh session.

Version 2. Changes since version 1 are listed at section 13.

Read sections 1 to 4 before changing anything. Section 9 is the outstanding work.

---

## 1. What this is

A tool that produces a letter of engagement for a new or prospective client. The user picks a client type and ticks the services, fills a short form, and gets a Word document on the firm's own letterhead. It is a prototype and will become a feature inside PracticeOS.

It replaces a manual process in which the firm opened the most recent similar letter, overtyped the client details and sent it. Fifteen such letters were supplied as the starting point.

**Single file:** `engagement-letter.jsx`, about 350KB, a React component with no build step and no backend. It runs as a chat artefact.

---

## 2. Architecture, and why

```
SEED_LIBRARY  (all clause text and layout, as data)
      |
   assemble(state, LIB)      one content model, conditions resolved,
      |                      numbering computed, cross references resolved
      +--> toHtml(model)     screen preview and HTML download
      +--> docxBody(model)   -> toDocx()            standalone .docx
                             -> toDocxOnTemplate()  merged into the firm's own .docx
```

Three rules that must not be broken:

**Clause text is data, not code.** Everything the letters say lives in `SEED_LIBRARY` and is exported and imported as JSON. Nothing about the wording is in the rendering logic.

**Numbers are computed, never typed.** No clause body contains its own clause number. Numbering is assigned at render. Cross references resolve by clause **title**, not by number, so splitting or removing a clause renumbers everything and the references follow. This was a live defect in the original letters, where "paragraph 16" was typed by hand.

**One builder per output format.** There is exactly one Word body builder, `docxBody`. There were briefly two and it caused three separate faults. Do not copy it again. If two outputs differ only by a value, the value becomes a parameter.

**Appendix letters are computed, never typed.** `plan()` walks the selected schedules in order and assigns 1A, 1B, 1C and so on. Schedule headings carry the placeholder `{{appx}}`, resolved per schedule from the same function that builds the covering letter's service list, so the two cannot disagree. The sequence runs 1A to 1J. Never type an appendix letter into a heading.

HTML and Word are genuinely separate emitters and should stay that way: a repeating margin letterhead is a header part in Word and fixed positioning in a browser. They share the content model, not the output.

---

## 3. The letterhead, which is the part most often got wrong

Do not reconstruct the letterhead in HTML or CSS. Several days were lost doing that.

The firm uploads its own `.docx` or `.dotx`. `readZip()` unpacks it, `mergeIntoTemplate()` replaces only the contents of `<w:body>` in `word/document.xml` and leaves every other part untouched, including `<w:sectPr>`. That section element holds the page size, the margins and the header and footer references, so the letterhead survives because it is never touched.

The uploaded file is remembered between sessions in `window.storage` and `harvestLetterhead()` reads the logo, strapline, names, office block and footer out of it so the HTML preview follows the real artwork.

Page geometry, taken from the firm's own section properties, in twips:

| Setting | Value |
|---|---|
| Page | 11904 x 16836 (A4) |
| Margins | top 2016, right 3024, bottom 1440, left 1296 |
| Header / footer | 1440 / 720 |
| Default tab stop | 720 |

The 53.3mm right margin exists to make room for the vertical letterhead column. `<w:titlePg/>` is set: page one uses the full branded column, later pages a small mark at the top right.

---

## 4. Typography, measured from the source

| Element | Value |
|---|---|
| Body font | Arial |
| Covering letter and schedules | 10pt |
| Terms of business | 9pt |
| Line spacing | single (240), headings 1.5 (360) |
| Spacing after paragraphs | **zero** |
| Justification | both |

Separation between blocks is achieved with **empty paragraphs**, not spacing-after. This is the single most important formatting fact. `blankLinesAfter(b, next)` implements the default rule; any block can override with `gapAfter`.

Indents, in twips. These vary by section and were established by measuring the rendered original:

| Context | Indent | Hanging |
|---|---|---|
| Numbered clauses, covering letter and appendices | 540 | 540 |
| Numbered clauses, addendum | 450 | 450 |
| Third-level clauses, addendum | 1080 | 630 |
| Schedule headings, appendices | 540 | 540 |
| Schedule headings, Schedule A and B, Sub-Appendix A | 450 | 450 |
| Bullets, first level | 990 | 450 |
| Bullets, second level (hollow "o") | 1440 | 450 |
| Lettered list a) to k), Appendix 1C | 990 | 450 |
| Items under e) and j), Appendix 1C | 1440 | 450 |
| Indented list items, Schedules A and B | 450 | flat |

Different sections were drafted at different times against different settings. Do not assume one value applies everywhere. **Measure the original before changing an indent.**

---

## 5. Verifying a change

The single most common failure in this project was reporting a change as done because the code had been written. Do not do this.

```bash
# render the docx, then measure the rendered output
soffice --headless --convert-to pdf letter.docx
pdftotext -bbox letter.pdf -            # word coordinates
pdftotext -layout letter.pdf -          # visual approximation only
```

Compare the coordinate of a word in the generated PDF against the same word in the original PDF. `pdftotext -layout` is an approximation and has produced false readings more than once.

If a change has no visible effect, that is evidence of a bug, not a reason to move on. Twice the cause was a model builder silently dropping block properties.

---

## 6. Data model

`SEED_LIBRARY` currently holds 42 covering letter blocks, 27 terms clauses with 122 paragraphs, and 17 schedules with 412 paragraphs, plus `letterhead` and `type`. The file is about 350KB, of which roughly 300KB is the library.

Block properties: `k`, `t`, `ind`, `hangW`, `flat`, `bold`, `gapAfter`, `gapBefore`, `nogap`, `brk`, `rtab`, `head`, `cells`, `when`, `id`.

Block kinds:

| Kind | Meaning |
|---|---|
| `clause` | numbered clause heading |
| `para` / `p` | numbered paragraph |
| `sub` / `p3` | third-level numbered paragraph |
| `parahead` / `h2` | numbered bold sub-heading |
| `shead` | schedule heading |
| `snum` | numbered schedule paragraph |
| `cont` / `plain` | unnumbered paragraph |
| `bullet` / `bullet2` | first and second level bullets |
| `tabitem` | indented list item, no marker |
| `table` | one table row, `cells` array, `head` for the header row |
| `signature` | Lucida Handwriting, bold |
| `rule` / `addr` / `spacer` | dotted rule, address line, blank |

Inline markup inside `t`: `**bold**`, `__underline__`, `\t` for a real tab. Web addresses are underlined automatically. Placeholders are `{{name}}`; cross references are `{{xref:dp}}`, `{{xref:liab}}`, `{{xref:tp}}`.

`{{appx}}` is a special placeholder used only in schedule headings. It resolves to the schedule's computed appendix letter. Thirteen headings carry it. The Addendum, Sub-Appendix A, Schedule A and Schedule B are named rather than lettered and sit outside the sequence, deliberately.

Schedule keys: `A1_ltd`, `A1_uninc_sole`, `A1_uninc_psh`, `B_ct_novat`, `B_ct_vat`, `B_ct_novat_payroll`, `B_ct_vat_payroll`, `B_sa_legacy_novat`, `B_sa_legacy_vat`, `B_sa_mtd`, `B_ind_legacy`, `payroll`, `addendum`, `subappA`, `schedA`, `schedB`.

---

## 7. Decisions taken with the client

Do not reverse these without asking.

- Every clause numbers its paragraphs, including single-paragraph clauses. Clause 16 becomes 16.1.
- Singular and plural follow **client type**, not the number of signatories. Company, sole trader and individual singular; partnership plural.
- One signature block for a company however many directors, one per partner for a partnership.
- Company and partnership letters open "Dear Sir/Madam".
- Clause 2.1: tax year for individuals, accounting period for others, trailing phrase suppressed where payroll is the only service.
- Clause 2.3: "from one appointment to another" for individuals only; "signing and returning" everywhere.
- The personal countersignature on company letters is **removed** in the proposed version and retained in the reproduction version.
- File reference: `PARTNER / [MANAGER] / GENERATOR / CLIENTREF`, manager segment and its slash omitted when none selected.
- Client reference: initial letter plus three digits, with a trailing letter for an individual connected to that client, inherited from the parent entity rather than their own surname. Mrs M L Smith is K154B because she is connected to client K154.
- Clause library governance: Mark Spafford custodian, Karl Goddard approver.
- Audit registration assumed current, clause 23 retained with a lead-in and annual verification.
- June 2025 footer on Appendix 2: **left out**, by agreement.

---

## 8. Deliberate departures from the source

Each of these fixes a fault rather than reproducing it. Flag if reversing.

- Seventeen typographical corrections, including "evidence of Your identify", "not usual identify fixed fees", "act of other clients", and the letterhead address, which reads Elliot Court in the letters and Elliott Court at Companies House, the ICAEW register and the firm's own footer.
- Money Laundering Regulations 2007 updated to the 2017 Regulations as amended.
- Clause 16 split so "Exclusion of Liability for Loss Caused by Others" is clause 17; everything below renumbered to 27.
- Clause f) in Appendix 1C joined into one paragraph. It was split mid-sentence, so the first fragment was being stretched by justification.
- The paragraph after j) is now clause k).
- The acceptance block gets a real page break. In the source it reaches page three through eleven consecutive empty paragraphs, which breaks with a longer client name.
- Addendum date lines use a right-aligned tab stop rather than six consecutive tabs, which wrapped on longer client names.
- Data processor Addendum retained in the reproduction, recommended for withdrawal in the proposed version.

---

## 9. Outstanding work

**a. Terms clause 12.4 sentence splitting.** The definitions under 12.4.1 were partly rejoined but the clause needs re-extracting from the source XML the way the addendum was, preserving paragraph boundaries and inline bold. See `harvestLetterhead` and the addendum extraction for the method.

**b. Re-extract the whole library preserving inline bold.** Bold inside paragraphs was being flattened everywhere until the addendum was redone. Other schedules and the terms of business almost certainly still have losses.

**c. A measured full-document comparison.** Rather than fixing faults as they are spotted, walk every paragraph of the original against the generated output, compare coordinates, and correct the differences in one pass.

**d. Layout fields in the Templates tab.** The editor exposes only text and kind. `ind`, `hangW`, `gapAfter`, `bold` and the rest are in the library but not reachable from the interface.

**e. PDF endpoint.** `PDF_ENDPOINT` at the top of the file is empty. The PDF button builds the same .docx the Generate button produces, merged onto the firm's letterhead, then posts it to that endpoint as multipart form data under the field name `file` and downloads whatever comes back. Point it at a route that runs `soffice --headless --convert-to pdf` and returns the bytes, and the button gives a finished PDF. Until then it downloads the .docx with a note to use Save as PDF from Word.

A browser cannot convert a .docx. There is no library and no standard that allows it, because it needs a layout engine that understands Word's page model. The earlier button rendered HTML instead, which is why the output looked wrong. Do not attempt to solve this client side.

**f. Login and settings lock.** Requested. A client-side gate is not security and should be labelled as a convenience lock. Real access control is Supabase Auth in PracticeOS.

**g. Postcode lookup.** Deferred. Note that postcodes.io is free but returns geography, not deliverable addresses; house-level addresses need a PAF licence through getAddress.io, Ideal Postcodes or Loqate. The Companies House API is free and higher value for company clients, filling name, registered office, directors, PSCs and accounting reference date from a company number.

**h. Compliance items**, which are not software work and are set out in `LOE_Compliance_Gaps_and_Differences.docx`. The most serious is consumer cancellation rights under the Consumer Contracts Regulations 2013, absent from all fifteen letters and directly relevant because the tool is designed to sign clients up away from the office.

---

## 10. What is still in code rather than data

- `VOCAB`, the client-type vocabulary: salutation, entity descriptor, singular and plural forms, period wording.
- `PRONOUN`, title to pronoun mapping.
- `blankLinesAfter`, the default spacing rules.
- `plan()`, which schedule is selected for which combination.
- Three generated blocks: the service list, the signature blocks and the address block, because their length depends on the engagement.
- Default indents and the keep-with-next rule.

---

## 11. Files

| File | What it is |
|---|---|
| `engagement-letter.jsx` | the app |
| `addendum-check.pdf` / `.docx` | current full payroll letter on the firm's letterhead |
| `individual-letter.pdf` / `.docx` | current individual client letter |
| `blank-letterhead.docx` | the firm's letterhead with the body emptied, the file to upload as the template |
| `LOE_Review_and_Change_Register.docx` | what changed from the fifteen letters and why, for partner sign-off |
| `LOE_Defects_and_Recommendations.docx` | 21 defects of substance in the letters as they stand |
| `LOE_Compliance_Gaps_and_Differences.docx` | UK compliance gaps and a per-letter difference table |
| `letters-as-supplied.jsx` | earlier prototype reproducing the fifteen letters verbatim, kept for the partner review exercise |

---

## 12. Working notes

The client is an accountant, not a developer, and reviews output rather than code. He is direct about faults and expects them acknowledged rather than explained away.

Three habits worth keeping. State plainly when something has not been verified. When a fix does not work, find the cause rather than trying another value. And when a change is a departure from the source rather than a correction of the generated output, say so at the time.

The clause library carries a great deal of layout detail that nobody but the developer has reviewed. When the partners sign off, they should read the exported library rather than the rendered letter, because the extraction faults found so far, a dropped "dated", split sentences, lost bold, all read perfectly well on the page.

---

## 13. Changes since version 1

**Appendix lettering made dynamic.** Schedule headings had the appendix letter typed into them, carried over from whichever original letter each was extracted from. When a service was selected on its own, the covering letter correctly called it appendix 1A while the schedule page still read 1B or 1C. Thirteen headings now use `{{appx}}` and resolve from `plan()`. Verified across six combinations, including company payroll only, company tax only, and individual with tax and Making Tax Digital. The sequence was extended from four letters to ten so the VAT, P11D and Companies House schedules can be added without further change.

**Individual and Making Tax Digital schedules normalised.** These had been missed when the other schedules were corrected. Numbered clauses hang at 540, sub-headings are bold, unnumbered text sits at the clause text position, and split sentences are rejoined. "2 Our Responsibilities" had come through as an ordinary line rather than a heading. Clause 1.5 read "liable to register **you** for VAT" because the object pronoun that suits a company reads wrong for a person; it now reads "register for VAT" for individuals and unincorporated clients and "register it for VAT" for companies.

**The PDF button rebuilt.** It previously printed the reconstructed HTML, which is why it produced a document that did not match the Word output. It now builds the .docx first and posts it to a converter. See section 9e.

**Panel position fixed** on the left; the toggle is removed.

**Header revised.** "Letter of Engagement" capitalised, and the file reference moved into its own bordered box at 15pt with a small label above it.

**Underline markup added,** `__like this__`, alongside `**bold**`. Used for "pensionable pay" in Appendix 1C clause 1.4 k), which is a hyperlink in the source pointing at a path on the firm's own network drive.

**Appendix 1C corrections.** Clause 1.4 is a bold heading in its own right, and had been silently failing to change because the pattern matching it required a tab where the text has a space. Clause f) was two paragraphs split mid-sentence, so justification stretched the first fragment across the full width; the two are now joined. The paragraph after j) is now clause k). The lettered list runs a) to k) at 990 with a 450 hang, with the items under e) and j) as hollow bullets at 1440.

**Terms of business model builder fixed.** It was copying only the text and a couple of properties out of the library and discarding `gapAfter`, `ind`, `bold` and `head`, so changes to anything in Appendix 2 had no effect on the output. Five reported fixes had appeared to work and had not. It now applies one `extra()` function to every block kind.

**Table headers** are bold and shaded, which required the same fix: the `head` flag was set in the library but dropped when rows were copied into the model.

---

## 14. A note on verification, worth reading

Three times in this project a change was reported as done when it was not. In each case the code had been written, the library showed the new value, and the output was unchanged, because a model builder was silently discarding the property.

The lesson is in section 5 and bears repeating here. Check the rendered output, not the code. Measure a coordinate in the generated PDF against the same word in the original. And when a change appears to have no effect, treat that as evidence of a bug rather than as a reason to try a different value.
