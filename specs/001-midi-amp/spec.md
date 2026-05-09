# Feature Specification: MIDI Amp Control

**Feature Branch**: `001-midi-amp`
**Created**: 2026-05-09 (retrospective)
**Status**: Implemented (v1.0.0)
**Input**: `routes.py`, `screen.html`, `screen.js`, `README.md`.

## User Scenarios & Testing

### User Story 1 — Auto-switch amp preset on tone change (P1)

As a guitarist whose multi-effects amp accepts MIDI, I want my hardware
preset to switch automatically when a song changes tones (Clean →
Distortion → Lead), so I don't need to tap a footswitch mid-song.

**Why this priority**: This is the plugin.

**Independent Test**: Connect a USB MIDI device that responds to PC.
Map the song's two tones to two PC numbers. Hit play, let the song
cross the tone change, watch the device switch presets at the chart's
tone-change time.

**Acceptance Scenarios**:

1. **Given** a Web-MIDI-capable browser and a connected device,
   **When** the song's `highway.getToneChanges()` reports a new
   `tone_key`, **Then** the plugin sends the mapped MIDI message
   (PC or CC) on the configured channel.
2. **Given** a tone has no mapping, **When** the song hits that
   tone, **Then** no MIDI is sent (silent skip, no error).

---

### User Story 2 — Configure mappings per song (P1)

As a user, I want a screen where I pick a song, see its tones, and
assign each tone a MIDI message (type, channel, CC#, value), with
auto-save and a Test button.

**Why this priority**: Without configuration the plugin can't fire.

**Independent Test**: Visit the MIDI screen, search for a song, click
it. Each tone in the song renders a row with msg_type / channel /
CC# / value fields. Edit a value — `POST /mappings/<filename>`
fires automatically. Reload — values persist.

**Acceptance Scenarios**:

1. **Given** a PSARC song with tones, **When** the user opens the
   editor, **Then** `GET /song-tones/<filename>` returns the
   tone list and `GET /mappings/<filename>` returns the saved
   mappings.
2. **Given** a mapping change, **When** the field's `change` event
   fires, **Then** `POST /mappings/<filename>` is called with the
   updated row and the DB upserts on `(filename, tone_key)`.
3. **Given** a sloppak song, **When** the editor loads,
   **Then** `/song-tones` returns `{tones: []}` and the editor shows
   "No tones found" (sloppaks have no RS-format tone manifest).

---

### User Story 3 — Test a mapping interactively (P2)

As a user dialling in mappings for a new amp, I want a Test button
per tone so I can confirm the device responds before relying on it
mid-song.

**Acceptance Scenarios**:

1. **Given** a saved mapping, **When** the user clicks Test, **Then**
   the same exact MIDI message that playback would send is emitted to
   the selected output device.
2. **Given** the user is on the global "Test MIDI Output" panel,
   **When** they pick type / channel / CC# / value and click Send,
   **Then** that message is emitted unchanged.

---

### User Story 4 — Surface device + browser-support failure modes (P3)

As a user, I want clear errors when Web MIDI is unsupported, MIDI
access is denied, or no devices are connected.

**Acceptance Scenarios**:

1. **Given** Firefox, **When** the screen loads, **Then** a red
   "Web MIDI not supported" banner is shown and no further setup is
   attempted.
2. **Given** the user denied MIDI access, **When**
   `requestMIDIAccess` rejects, **Then** the error message is
   surfaced verbatim.
3. **Given** no MIDI outputs, **When** the device list is empty,
   **Then** an amber "No MIDI output devices" banner is shown and
   the test panel is hidden.

## Functional Requirements

- **FR-001**: Schema —
  ```
  CREATE TABLE midi_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    tone_key TEXT NOT NULL,
    tone_name TEXT,
    midi_channel INTEGER DEFAULT 0,
    msg_type TEXT DEFAULT 'cc',     -- 'cc' | 'pc'
    cc_number INTEGER DEFAULT 0,
    value INTEGER DEFAULT 0,
    UNIQUE(filename, tone_key)
  )
  ```
- **FR-002**: `GET /api/plugins/midi_amp/mappings/<filename:path>`
  returns saved mappings for a song, ordered by `tone_key`.
- **FR-003**: `POST /api/plugins/midi_amp/mappings/<filename:path>`
  upserts on `(filename, tone_key)`.
- **FR-004**: `DELETE /api/plugins/midi_amp/mappings/<id>` removes a
  single mapping.
- **FR-005**: `GET /api/plugins/midi_amp/song-tones/<filename:path>`
  reads the PSARC's `*.json` entries, walks
  `Entries[*].Attributes.Tones[]`, returns
  `{tones: [{key, name, arrangement}]}` deduped by key.
  Sloppaks return `{tones: []}` short-circuit.
- **FR-006**: SQLite uses WAL journal mode and a process-wide
  `threading.Lock` for writes (`_lock`).
- **FR-007**: Frontend: Web MIDI device picker persists choice in
  `localStorage` under key `midi_output_id` (note: device choice is
  per-browser; mappings are server-side).
- **FR-008**: `midiSend(channel, msgType, ccNumber, value)` builds
  raw MIDI bytes:
  - `msgType === 'cc'`: `[0xB0|ch, ccNumber&0x7F, value&0x7F]`.
  - `msgType === 'pc'`: `[0xC0|ch, value&0x7F]` (cc_number ignored).
- **FR-009**: The plugin MUST listen for highway tone-change events
  during playback and call `midiSend(...)` with the row matching the
  current tone. [NEEDS CLARIFICATION: the actual auto-switching
  hook is not visible in the snippet read; confirm whether it lives
  in `screen.js` lower than line 200 or in a separate file.]
- **FR-010**: The test panel MUST send the same byte sequence as
  playback would — no parallel codepath.

## Out of Scope

- Sysex.
- MIDI input (clock, beat, learning).
- Bank Select MSB/LSB as separate first-class fields. **The README
  documents these but the schema and UI use only `cc_number` +
  `value`.** A user wanting bank select sends a CC#0 / CC#32 row
  alongside the PC row.
- Mapping presets shareable across songs.
