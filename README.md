# GridPass native layout feasibility gate

A source-only implementation for transferring selected DBeaver table-layout
settings. There is no product UI or completed layout-compatibility claim yet.

The core accepts explicit saved-data-filter.xml bytes and selected source/target
entry IDs. It transfers only column position, visibility, pinning and sort
priority to an existing target with the same unique flat column names. Target
identity, bindings, predicates, opaque values and all other entries stay the
target's own. It never opens a database, scans a workspace, installs files, runs
SQL or copies a source expression. The output is a new target copy and receipt.

DBeaver reads Java-serialized values internally. GridPass never invokes Java
deserialization: pin strings are matched against a finite whitelist of canonical
Integer values 0–255 emitted by the verified official bundled JDK. Other target
values remain opaque and unchanged. This does not certify an entire file as safe
to load in DBeaver. Use trusted target files and close DBeaver before manually
applying a reviewed copy; its delayed save can overwrite external edits.

## Native evidence and pending gate

The bounded compatibility checkpoint passed at
`50c88a5730ceaacf0847a93da00b324dbf2ffb59`, in
[run 37565607740](https://github.com/Masanori-Spec/grid-pass/actions/runs/37565607740).
The official DBeaver Community Edition 26.2.2 GUI loaded the pinned local
SQLite JDBC 3.53.4.0 driver in a disposable profile. All five original rows were
copied from the real native grid, all 256 JDK Integer encodings matched, and the
application exited normally with code 0 and no fatal native log marker. Real
accessibility trees and screenshots were independently reviewed. The earlier
forced-cleanup crash and harness lookup/race failures do not establish a layout
result; the accepted lifecycle checkpoint is identified separately here.

The current hosted gate must author source, target and unrelated layouts through
real GUI cell filters, layout controls and Save as default filter. Target's
native NOT_EQUALS/String C predicate and different column metadata are
preservation sentinels. After normal close, the production core patches only the
existing target entry. The unchanged native file loader must show exact target
rows/column order, save, exit and reload in a fresh process. Visibility, position,
pin and sort fault controls must each show their precise native effect and fail
the positive oracle. This full gate remains pending execution and independent
evidence review. It must pass before product UI work.

The test opens only original synthetic SQLite fixtures in the hosted runner.
Official binaries and the compiler output remain test-only and are excluded
from source packages and workflow artifacts. There is no native validation
endpoint for arbitrary user files. See [the full contract](docs/native-contract.md).

## Supported core profile

Run `npm ci --ignore-scripts` and `npm test` for 74 core checks. Run
`python3 scripts/verify-layout.py selftest` for the independent protected-byte
oracle's five fault controls. Inputs require
XML 1.0/UTF-8, at most 4 MiB per file, bounded XML depth/elements, and at most 256
ordinary flat columns in a selected entry. Names must exactly equal referenced
native binding names; quoted-name distinctions are currently unsupported.
The advancing XML lexer caps names at 128 characters, attributes at 64 per
element and 120,000 total, and lexical tokens at 80,000. Malformed and large
inputs have isolated timeout/memory regressions; markup in comments stays inert.
Positions are a complete zero-based permutation, active sort priorities are
unique, and pin indices are distinct whitelist values. Valid pin gaps are
preserved. Unknown selected structures, DTD/entity declarations, ambiguous
identities and noncanonical pin strings fail closed. This is not database schema
validation or a whole-file safety check.

The product patch preserves protected bytes; subsequent native saves are checked
for protected semantics, not whole-file byte identity. Original code and
synthetic fixture content have no reuse license grant. Existing third-party
ownership notices apply only to their dependencies:
[THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
