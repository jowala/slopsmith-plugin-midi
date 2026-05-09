# Implementation Plan — MIDI Amp Control

Single-screen plugin with five backend endpoints, SQLite persistence,
and Web MIDI on the frontend.

## Files

- `plugin.json` — id `midi_amp`, declares screen / script /
  settings.html / routes.
- `routes.py` (136 lines) — backend.
- `screen.html` (42 lines) — config screen.
- `screen.js` (324 lines) — Web MIDI + mapping editor + playback
  hook.
- `settings.html` (4 lines) — placeholder settings panel.
- `__pycache__/` — runtime artefacts (gitignored).

## Backend

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/plugins/midi_amp/mappings/<filename:path>` | GET | Read saved mappings, ordered by `tone_key`. |
| `/api/plugins/midi_amp/mappings/<filename:path>` | POST | Upsert mapping on `(filename, tone_key)`. |
| `/api/plugins/midi_amp/mappings/<mapping_id>` | DELETE | Delete by id. |
| `/api/plugins/midi_amp/song-tones/<filename:path>` | GET | Walk PSARC JSON for tones. Sloppak short-circuit. |

### Schema (created on first connect)

```sql
CREATE TABLE midi_mappings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  tone_key TEXT NOT NULL,
  tone_name TEXT,
  midi_channel INTEGER DEFAULT 0,
  msg_type TEXT DEFAULT 'cc',
  cc_number INTEGER DEFAULT 0,
  value INTEGER DEFAULT 0,
  UNIQUE(filename, tone_key)
);
```

WAL mode; module-level `_conn` plus `_lock = threading.Lock()` for
writes.

### Tone discovery

- Sloppak (filename ends `.sloppak`): return `{tones: []}`.
- PSARC: `read_psarc_entries(path, ["*.json"])`, walk
  `Entries[*].Attributes`. Skip arrangement names `Vocals`,
  `ShowLights`, `JVocals`. Tolerate trailing-comma JSON via a
  one-shot `re.sub` pass.

### Setup contract

```python
def setup(app, context):
    _db_path = str(context["config_dir"] / "midi_mappings.db")
```

## Frontend

`screen.js` is split into:

1. **Web MIDI bootstrap** (`midiInit`, `_updateMidiDevices`,
   `midiSelectDevice`).
2. **Raw send** (`midiSend(channel, msgType, ccNumber, value)`).
3. **Test panel** (`midiTestSend`).
4. **Mapping editor** (`midiSearchSongs`, `midiEditSong`, auto-save
   via `change` listener on `.midi-field`, per-tone Test
   `midiTestMapping`).
5. **Playback hook** — listens for tone changes during playback
   and triggers `midiSend(...)` with the row matching the current
   tone. (Lower half of `screen.js`.)

Persisted in `localStorage`:

- `midi_output_id` — preferred output device id.

## Integration with Slopsmith Core

- **`psarc.read_psarc_entries`** — shared PSARC reader.
- **Library API** — `/api/library?q=...` for song search.
- **Highway hooks** — `highway.getToneChanges()` for playback-time
  tone awareness.
- **Player controls** — README mentions a "MIDI" button injected
  into player controls; assumed wired in `screen.js` similarly to
  `metronome` / `nam_tone`.

## Out of Scope / Deferred

- Sysex (would need `sysex: true` in `requestMIDIAccess` and is
  amp-specific).
- MIDI input (clock sync, learn-mode mapping).
- Mapping presets that travel across songs (could be a follow-up:
  add a `preset_id` column and a Presets table).
- Tests — none in repo.
