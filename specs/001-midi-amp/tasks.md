# Tasks — MIDI Amp Control

## US1 — Auto-switch on tone change (P1)

- [DONE] T101 Schema + WAL + `(filename, tone_key)` UNIQUE.
- [DONE] T102 `midiSend(...)` with CC / PC byte building.
- [OPEN] T103 [P] Confirm + document the playback-time hook
  exact mechanics (where in `screen.js` does the tone-change
  listener live? polling vs event?). Spec marked
  [NEEDS CLARIFICATION].

## US2 — Configure mappings (P1)

- [DONE] T201 GET / POST mappings.
- [DONE] T202 DELETE mapping.
- [DONE] T203 Tone discovery via PSARC walk.
- [DONE] T204 Sloppak short-circuit (no tones).
- [DONE] T205 Mapping editor UI with auto-save on change.

## US3 — Test interactively (P2)

- [DONE] T301 Per-tone Test button.
- [DONE] T302 Global Test panel.
- [DONE] T303 Test sends the same byte sequence as playback
  (single `midiSend` codepath).

## US4 — Browser / device support failures (P3)

- [DONE] T401 Firefox detection + banner.
- [DONE] T402 Permission rejection surfaced.
- [DONE] T403 Empty device list banner.

## Cross-cutting

- [DONE] T501 SQLite `_lock` around writes.
- [DONE] T502 Per-browser device persistence in `localStorage`.
- [OPEN] T503 [P] **Update README**: drop the "Bank MSB / Bank LSB
  / Program" table, document the `cc | pc` schema and the
  CC#0 / CC#32 + PC pattern for Bank Select. Drift from clarify.md
  Q1.
- [OPEN] T504 [P] Add tests — mock SQLite, exercise upsert path,
  verify byte construction in `midiSend`.
- [OPEN] T505 [P] Mapping presets reusable across songs
  (separate Presets table, foreign key on mapping rows).
- [OPEN] T506 [P] Show device latency / buffer info so users can
  trust the timing.
