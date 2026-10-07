# GridPass verification record

## Product boundary

GridPass edits an explicitly selected existing target entry in supplied
DBeaver saved-data-filter XML. Only position, visibility, pin and sort fields
are copied. Target identity, bindings, conditions, opaque serialized values and
all unselected entries stay the target's own. No database, SQL, native consumer,
workspace discovery or automatic application runs in the offline product.

Supported input is deliberately narrow: XML 1.0/UTF-8; ordinary flat bindings;
exact unique names; complete positions; at most 256 selected columns; canonical
Integer 0–255 pin strings. No generic Java object deserializer exists in the
product. Untouched target bytes are not a security certification.

## Accepted runtime

Tested implementation commit: `804bbe986a49c19fa26fecfd4222b1351f1ccaac`.
The documentation/evidence closeout preserves all tested implementation, harness,
workflow and standalone HTML bytes from that commit.

| Evidence | Exact identity |
| --- | --- |
| Browser/native run | [37577834267](https://github.com/Masanori-Spec/grid-pass/actions/runs/37577834267) |
| Native-only run | [37577834260](https://github.com/Masanori-Spec/grid-pass/actions/runs/37577834260) |
| Browser artifact | 11463725750 · 25 members · SHA-256 `0df3166840fe342fb627842ba76378be035ff29510aafdf6f925d11ab83535e4` |
| Browser/native artifact | 11464256069 · 179 members · SHA-256 `4b374035e1d9e4c0e73e1fe5cc8325493086341b58bfe7d6f5214ebfb3982109` |
| Native-only artifact | 11464001313 · 153 members · SHA-256 `883e658e7b40e024f61047cbb19b3ec7ac85a6ae756b3ada50484a3573489794` |
| Standalone HTML | SHA-256 `aa8709a6772f5db5031a439771332d1acc0d6f0e5d8bddbeea388c86915c6ca5` |
| Actual browser XML | 4,408 bytes · SHA-256 `e65c4d1585e31ee1ba7c1f7b8292452ed61654a57e8250883aec0c386b3f2639` |

The full 25-file browser handoff is identical in the combined artifact. The
native positive input is the downloaded browser XML itself; no direct-core
substitute replaces it. Its receipt is likewise passed unchanged. Native GUI
re-authoring must reproduce the exact original synthetic fixture first.

## Independent oracles

The browser harness uses handwritten literal byte edits and a fixed expected
SHA, separate from the production editor. Its 34 cases cover explicit selection,
keyboard chooser/export/reset, same-file reselection, no-op/repeated output,
exact receipt fields, inert labels, blocked XML/pins/bindings/limits, delayed
read/hash invalidation, no page or console errors, and zero network requests.
The actual Chrome main-process command is retained and checked for enabled
sandboxing. The empty-input test is a dispatched empty change event, not a claim
about every operating system's native dialog cancellation behavior.

The independent Python oracle checks the entire target after masking only
allowed constraint layout attributes, pin elements and necessary self-closing
wrappers. Filter-level SQL expressions, inter-element bytes, comments, bindings,
opaque values and all outside-target bytes remain protected. Source TEXT versus
target VARCHAR metadata is checked literally. Canonical pin strings are checked
against every Integer emitted by the pinned official bundled JDK, without
reading arbitrary Java objects.

The fixed native data gives positive target IDs `[5, 2, 3, 1]`, with id pinned,
status before name, note hidden, status ascending then id descending. Target
status-not-C stays in place; source id-greater-than-2 never leaks into the target.

| Controlled fault | Required visible native effect |
| --- | --- |
| Reveal note | Exact note values become the fourth visible column |
| Swap name/status positions | Visible order changes to id/name/status; dialog order changes too |
| Add name pin1 | Visible order changes to id/name/status while dialog positions remain id/status/name |
| Change id to ascending | Exact target ID order becomes `[2, 5, 1, 3]` |

Every fault must match its own literal expectation and fail the positive grid
expectation. Positive save/fresh reopen must match again. The paired runs pass
six modes each and all 14 processes exit normally. Actual positive/reloaded pin
checkboxes and the id+name pin fault were inspected in original pixels.

## Visual evidence

The reviewed viewports are desktop 1440px and mobile 390/320px in both languages.
The table scrolls horizontally; the rightmost header and cells remain reachable.
The Japanese narrow-screen headline has two complete lines and the scope title
one. Both fixture print reviews are complete single A4 pages. This is a bounded
viewport/fixture review, not a blanket accessibility or arbitrary-document print
certification.

- [English desktop](evidence/browser/01-en-desktop.png)
- [Japanese desktop](evidence/browser/01-ja-desktop.png)
- [Japanese 320px](evidence/browser/03-ja-320-left.png)
- [English 320px right edge](evidence/browser/03-en-320-right.png)
- [Japanese print PDF](evidence/browser/02-ja-review.pdf) and [rendered page](evidence/browser/02-ja-review.png)
- [English print PDF](evidence/browser/02-en-review.pdf) and [rendered page](evidence/browser/02-en-review.png)
- [Blocked input](evidence/browser/04-en-error.png)
- [Actual native target grid](evidence/native/positive/actual-target-grid.png)
- [Freshly reopened native pin state](evidence/native/positive-reloaded/actual-target-settings.png)
- [Native added-pin fault](evidence/native/negative-pin/actual-target-settings.png)

## Native normalization and startup failures

The output patch itself preserves all protected bytes, including twelve false
pseudo-column flags in the original fixture. A later DBeaver save omits exactly
eight such flags from the unopened source/unrelated bindings. That observed
false-to-absent change is recorded explicitly per mode. Target nonlayout
semantics and every other source/unrelated semantic remain exact; native saves
are not claimed to preserve whole-file bytes.

Two full-gate startup attempts failed inside GTK/GObject before the current
paired success. The first had one recorded unchanged-head retry. After the
second, identical retries stopped and a bounded X11 startup-settling experiment
was added before accessibility traversal. The successful runs record seven
readiness checks each, with at least 12 seconds elapsed and six seconds of a
stable window, under a 60-second polling bound. Fatal logs/nonzero exits remain
failures. Only safe runtime/current-thread crash frames may be retained; raw
crash reports, registers, memory dumps and environment sections are excluded.

These passing runs do not establish the original crash cause or promise general
DBeaver startup reliability. Earlier failures are retained separately in the
verification history; see [native-checkpoint.md](native-checkpoint.md).

All copied evidence is byte-for-byte from the accepted hosted artifacts, with
original member paths and hashes in [evidence-provenance.json](evidence-provenance.json).
