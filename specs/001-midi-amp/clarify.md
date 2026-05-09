# Clarifications — MIDI Amp Control

## Q1. README mentions Bank MSB / Bank LSB / Program — schema has CC# / value / msg_type. Which is right?

**A.** The schema and UI are right. The README's table is from an
earlier draft. To send Bank Select today, the user creates two CC
rows (CC#0 = MSB, CC#32 = LSB) followed by a PC row. The README
should be updated to match. **Drift item.**

## Q2. Why is mapping storage server-side but device choice
client-side?

**A.** Mappings need to follow the song across browsers / users in a
shared install. Device IDs are browser-scoped (and machine-scoped) —
storing them server-side would conflate "the install" with "this
particular browser's view of devices", which would break as soon as
two people on different machines used the same Slopsmith install.

## Q3. What happens on Firefox?

**A.** `navigator.requestMIDIAccess` is undefined; the screen shows
a red error banner and stops. Backend endpoints still work (mappings
can be edited), but no MIDI is sent.

## Q4. How does the plugin know when a tone changes during playback?

**A.** Via `highway.getToneChanges()` — the same surface the NAM Tone
Engine plugin polls. The implementation detail (poll interval, event
listener, etc.) is in the lower half of `screen.js`; the contract is
"on each tone-change boundary, look up the saved mapping for
`(filename, tone_key)` and fire `midiSend` with its fields".
[NEEDS CLARIFICATION: confirm the exact loop.]

## Q5. Why is the schema column called `cc_number` even when
`msg_type='pc'`?

**A.** Single-table simplicity. PC messages don't have a CC#; the
column is ignored by `midiSend` when `msg_type === 'pc'`. The DEFAULT
0 keeps the upsert simple.

## Q6. Why does `song-tones` deduplicate by key but include
`arrangement`?

**A.** Multiple arrangements (Lead, Rhythm, Bass) may reference the
same tone key — the user only cares about the unique tone for
mapping. The `arrangement` field is informational, shown in the UI
to help the user identify the tone.

## Q7. What happens if PSARC parsing fails?

**A.** `read_psarc_entries` raises `ValueError` / `OSError`; the
endpoint logs a warning and returns
`{tones: [], error: "Unsupported or invalid archive"}`. The frontend
treats `tones: []` as "no tones found" and shows the empty-state.
JSON-decode errors are tolerated by stripping trailing commas before
retrying — RS tone JSON files occasionally have those.
