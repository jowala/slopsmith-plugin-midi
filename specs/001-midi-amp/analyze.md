# Analysis — MIDI Amp Control

## Coverage

| Spec area | Implementation | Notes |
|---|---|---|
| FR-001 (schema) | `_get_conn` | OK. |
| FR-002 (GET mappings) | `get_mappings` | OK; ordered by tone_key. |
| FR-003 (POST mappings) | `save_mapping` | OK; INSERT OR REPLACE. |
| FR-004 (DELETE) | `delete_mapping` | OK. |
| FR-005 (song-tones) | `get_song_tones` | OK; sloppak short-circuit; trailing-comma JSON tolerated. |
| FR-006 (WAL + lock) | `_get_conn` + `_lock` | OK. |
| FR-007 (device persistence) | `localStorage.midi_output_id` | OK. |
| FR-008 (`midiSend`) | `screen.js:80` | OK; honours `msgType`. |
| FR-009 (auto-switch hook) | (lower `screen.js`) | **PARTIALLY VERIFIED** — see Drift. |
| FR-010 (test parity) | `midiTestSend` / `midiTestMapping` | OK. |

## Drift

1. **README's Mapping Example table** lists "Bank MSB", "Bank LSB",
   "Program" — these columns do not exist in the schema. Real
   columns are `msg_type`, `cc_number`, `value`. Fix the README
   (T503).
2. **README claims auto-save persists in SQLite** — accurate, but
   the README does not mention that **device choice** is in
   `localStorage` (per-browser). A user using two browsers will see
   the same mappings but different device defaults; documenting this
   prevents confusion.
3. **Auto-switch hook visibility** — only the first 200 lines of
   `screen.js` were inspected for this analysis; the playback hook
   that fires `midiSend` on tone change is presumed to live further
   down. T103 logs this for verification.

## Gaps

1. No tests. SQLite-backed plugins benefit from a quick pytest pass
   that creates an in-memory DB, exercises GET / POST / DELETE.
2. No `__pycache__` in `.gitignore` (visible in repo listing).
   Cosmetic.
3. `settings.html` is 4 lines — placeholder only. Either populate
   it (e.g. global default channel, scan-on-load delay) or drop
   `settings: { html: ... }` from `plugin.json`.
4. No way to clone a song's mappings to another song. For a multi-
   tone amp with consistent presets across the user's library, this
   is annoying.

## Recommendations

1. **Fix README drift** (T503).
2. **Add tests** for the four endpoints (T504).
3. **Verify the auto-switch hook**, document it explicitly in the
   plan, and consider extracting the tone-change handling into a
   small helper that `screen.js` re-uses for both Test and
   playback.
4. **Populate or drop `settings.html`.**
5. **Mapping presets** (T505) — a Presets table with a FK from the
   mapping row would let users say "this song uses my Helix Patch
   24 preset" once and reuse it.
