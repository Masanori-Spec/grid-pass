# Native feasibility checkpoint

The complete synthetic native gate was independently accepted at commit
`98af7fe469531006b24bf7fce4b53373a702caa6`,
[run 37571921415, attempt 2](https://github.com/Masanori-Spec/grid-pass/actions/runs/37571921415/attempts/2).

The official DBeaver CE 26.2.2 GUI authored the source, target and unrelated
saved entries. After normal close, the production core changed only the target
layout. The unchanged native file loader showed the expected columns, pins,
hidden note column and literal filtered/sorted IDs `[5, 2, 3, 1]`. A native save
and another fresh process preserved this result. Four exact visibility,
position, pin and sort-direction faults produced their distinct expected grid
outputs and failed the positive expectations. All seven native processes exited
normally. Real pin-checkbox screenshots were inspected independently.

The source name binding is TEXT; the target name binding is VARCHAR. Target
NOT_EQUALS/String C predicate bytes and every protected output byte remain
unchanged. The target never inherits the source's GREATER/id2 predicate. Native
save later omits exactly eight explicit false pseudo-column flags from unopened
source/unrelated bindings per mode. The output patch itself preserves all twelve
flags; that native normalization is checked separately and narrowly.

The accepted original workflow artifact is `11461871792`, 6,811,312 bytes,
SHA-256 `fe28577ae7b26ef84aef8cddbe3b78d76d06c97f0f19dd91f5c1611f3c2f3260`,
with 139 members. The retained native-authored fixture's SHA-256 is
`81ce1b826a09fc351188fc43554961e017bf80dd14ba40a1373c5f8c75c8a5c4`; the accepted
patched copy is `e65c4d1585e31ee1ba7c1f7b8292452ed61654a57e8250883aec0c386b3f2639`.

## Failed attempts remain part of the record

The earlier full run `37570609724` completed all native modes but its original
final oracle rejected the observed false-flag omission. That oracle was repaired
only after inspecting the actual outputs and official persistence code.

Attempt 1 of run `37571921415` suffered a real GTK SIGSEGV in
`gtk_widget_get_allocation` during the first fresh startup. Its cause is not
established. One explicitly recorded rerun of the same reviewed head passed the
whole gate; this is not a blanket native runtime stability guarantee. The raw
successful and failed artifacts and member hashes are retained in the private
verification backup. There is no automatic retry loop or suppressed fatal exit.

This checkpoint verifies the core with original synthetic fixtures. The offline
UI candidate and its actual browser download require their own fresh browser and
native acceptance before a completed product claim.
