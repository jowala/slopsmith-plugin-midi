"""MIDI Amp Control plugin — store tone-to-preset mappings per song."""

import json
import sqlite3
import threading
from pathlib import Path

_db_path = None
_conn = None
_lock = threading.Lock()


def _get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_path, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS midi_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                tone_key TEXT NOT NULL,
                tone_name TEXT,
                midi_channel INTEGER DEFAULT 0,
                msg_type TEXT DEFAULT 'cc',
                cc_number INTEGER DEFAULT 0,
                value INTEGER DEFAULT 0,
                UNIQUE(filename, tone_key)
            )
        """)
        _conn.commit()
    return _conn


def setup(app, context):
    global _db_path
    _db_path = str(context["config_dir"] / "midi_mappings.db")

    @app.get("/api/plugins/midi_amp/mappings/{filename:path}")
    def get_mappings(filename: str):
        conn = _get_conn()
        rows = conn.execute(
            "SELECT id, tone_key, tone_name, midi_channel, msg_type, cc_number, value "
            "FROM midi_mappings WHERE filename = ? ORDER BY tone_key",
            (filename,)
        ).fetchall()
        return [
            {"id": r[0], "tone_key": r[1], "tone_name": r[2],
             "channel": r[3], "msg_type": r[4], "cc_number": r[5], "value": r[6]}
            for r in rows
        ]

    @app.post("/api/plugins/midi_amp/mappings/{filename:path}")
    def save_mapping(filename: str, data: dict):
        conn = _get_conn()
        with _lock:
            conn.execute(
                "INSERT OR REPLACE INTO midi_mappings "
                "(filename, tone_key, tone_name, midi_channel, msg_type, cc_number, value) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (filename, data.get("tone_key", ""), data.get("tone_name", ""),
                 data.get("channel", 0), data.get("msg_type", "cc"),
                 data.get("cc_number", 0), data.get("value", 0))
            )
            conn.commit()
        return {"ok": True}

    @app.delete("/api/plugins/midi_amp/mappings/{mapping_id}")
    def delete_mapping(mapping_id: int):
        conn = _get_conn()
        with _lock:
            conn.execute("DELETE FROM midi_mappings WHERE id = ?", (mapping_id,))
            conn.commit()
        return {"ok": True}

    @app.get("/api/plugins/midi_amp/song-tones/{filename:path}")
    def get_song_tones(filename: str):
        """Get tone keys from a CDLC for mapping."""
        from psarc import read_psarc_entries
        dlc = context["get_dlc_dir"]()
        if not dlc:
            return {"error": "DLC folder not configured"}

        dlc_path = dlc.resolve()
        psarc_path = (dlc_path / filename).resolve()
        try:
            psarc_path.relative_to(dlc_path)
        except ValueError:
            return {"error": "Invalid path"}

        if not psarc_path.exists():
            return {"error": "File not found"}

        # Sloppaks don't carry RS-format tone manifests — they're a
        # stripped-down format with stems + arrangement JSON only. Return
        # an empty list rather than feeding a non-PSARC into the PSARC
        # parser (which 500s on the magic-byte check).
        if psarc_path.name.lower().endswith(".sloppak"):
            return {"tones": []}

        try:
            files = read_psarc_entries(str(psarc_path), ["*.json"])
        except (ValueError, OSError) as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to read PSARC %s: %s", psarc_path, exc)
            return {"tones": [], "error": "Unsupported or invalid archive"}
        tones = []
        seen = set()

        for path, data in sorted(files.items()):
            if not path.endswith(".json"):
                continue
            try:
                j = json.loads(data)
            except json.JSONDecodeError:
                import re
                text = data.decode("utf-8", errors="ignore")
                text = re.sub(r",\s*([}\]])", r"\1", text)
                try:
                    j = json.loads(text)
                except Exception:
                    continue

            for k, v in j.get("Entries", {}).items():
                attrs = v.get("Attributes", {})
                arr_name = attrs.get("ArrangementName", "")
                if arr_name in ("Vocals", "ShowLights", "JVocals"):
                    continue
                for t in attrs.get("Tones", []):
                    key = t.get("Key", "")
                    name = t.get("Name", key)
                    if key and key not in seen:
                        seen.add(key)
                        tones.append({"key": key, "name": name, "arrangement": arr_name})

        return {"tones": tones}
