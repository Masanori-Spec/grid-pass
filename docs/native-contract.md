# Native acceptance contract

## Purpose and current boundary

[DBeaver issue37999](https://github.com/dbeaver/dbeaver/issues/37999) requests
sharing table configuration. DBeaver already saves filters, and broad workspace
or account-backed project sync is a different existing route. This proposal
addresses only explicit entry-to-entry transfer of selected layout properties.
No exhaustive uniqueness claim is made.

The bounded GUI/SQLite bootstrap passed. The current workflow attempts the full
layout gate below. Product UI stays locked until the actual full evidence passes.

## Required full gate

Use official CE26.2.2 commit5171a0a5864591ee78225a216586fd7535b15085, exact Linux
x86_64 tar127,503,062 bytes SHA-256
27b39a79a69ec70f9f95c6ee3b68514fcc7677acef93287e8df8e13cc53384d5. Release API
metadata and actual bytes must agree before execution. Record bundled Java's
actual version. Pin the separate official JDBC asset; the DBeaver tag's
RELEASE Maven reference is not a reproducible driver version.

The real GUI must author three saved entries for source_table, target_table and
unrelated_table, all with columns id, name, status and note. Source layout has
id pinned first, status before name, note hidden, status ascending then id
descending. Target has its own predicate, bindings and different initial layout.
The unrelated entry is a preservation sentinel. Discover the actual emitted
configuration path inside the disposable workspace; do not guess objectId.

The fixed source predicate is authored from the native id=2 cell with the
Cell value action id>2. The target uses status<>'C' through its native cell
action, yielding NOT_EQUALS plus an opaque serialized String C. The unrelated
table has its own status='C' filter. Target name uses VARCHAR(40), while the
source uses TEXT, so copying source bindings would be detectable. The target
starts with name pinned and all four columns visible. Expected final target IDs
are [5,2,3,1]. Scope the no-leak check to the selected target; the source entry
itself remains in the original file and must stay unchanged.

After normal application exit and completed native persistence, apply the
product's copy to the existing target entry. Reopen the actual target table in a
fresh DBeaver process. Verify visible grid order, pinned state, hidden note and
literal filtered/sorted rows. Native-save again, exit and freshly reopen to
repeat those observations. The unchanged file loader must consume the result.
XML-only structural checks or copied consumer structures are insufficient.

Four separate controls must change visibility, position, pinning and sort
direction and visibly alter the expected native result. An independent oracle
checks exact non-layout target subtrees and all unrelated entries, and proves
the source predicate never appears in target output.

The four faults are: show note; swap name/status positions; add name as second
pin1 while retaining id pin0; and make id sort ascending. The pin fault must
change the actual grid to id,name,status while its visual-position dialog stays
id,status,name,note. The position fault changes both. Original predicate/value
bytes and other entries remain unchanged in every variant. After native save,
protected semantics are checked separately from product byte preservation.

## Product limits

At most256 flat columns, exact unique constraint-name sets, valid unique column
positions and sort priorities. Pin indices are distinct canonical Integer0–255
values; gaps are valid because native unpinning can leave them. Product code
compares a finite whitelist, never deserializes Java objects. Reject unknown or
noncanonical pin encodings, duplicated identities, nested/ambiguous bindings,
DTD or entity declarations, and unsupported selected structures. Opaque target
values are preserved, not interpreted or certified.

Only original synthetic fixtures go through native validation. No arbitrary
user configuration, real profile, credentials or database is opened. No source
build, vendor payload in public artifacts, security-setting changes or paid
services are needed. Original fixtures/code have no reuse license grant.

Primary source: [DataFilterRegistry](https://github.com/dbeaver/dbeaver/blob/5171a0a5864591ee78225a216586fd7535b15085/plugins/org.jkiss.dbeaver.ui.editors.data/src/org/jkiss/dbeaver/ui/controls/resultset/DataFilterRegistry.java),
[FilterSettingsDialog](https://github.com/dbeaver/dbeaver/blob/5171a0a5864591ee78225a216586fd7535b15085/plugins/org.jkiss.dbeaver.ui.editors.data/src/org/jkiss/dbeaver/ui/controls/resultset/FilterSettingsDialog.java),
[CLI](https://dbeaver.com/docs/dbeaver/Command-Line/).

The local JDBC registration uses the pinned source's
`-Ddbeaver.drivers.configuration-file` option. A provided custom local library
disables the driver's noncustom default Maven libraries; the clean disposable
profile has no later user-driver overrides. The probe requires no downloaded
profile jars and exact original rows copied from the native grid. See
[DataSourceProviderRegistry](https://github.com/dbeaver/dbeaver/blob/5171a0a5864591ee78225a216586fd7535b15085/plugins/org.jkiss.dbeaver.registry/src/org/jkiss/dbeaver/registry/DataSourceProviderRegistry.java)
and [DriverDescriptorSerializerLegacy](https://github.com/dbeaver/dbeaver/blob/5171a0a5864591ee78225a216586fd7535b15085/plugins/org.jkiss.dbeaver.registry/src/org/jkiss/dbeaver/registry/driver/DriverDescriptorSerializerLegacy.java).
The test-only whitelist generator writes fixed trusted Integers through
ObjectOutputStream; it accepts no arguments and never reads serialized objects.
