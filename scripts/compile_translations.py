"""Compile the project's singular-message gettext catalogue without GNU tools.

Run from the project root: python scripts/compile_translations.py
Supports multiline msgid/msgstr and ignores translator comments. Runtime uses
Django's standard gettext; this helper is only needed when editing translations.
"""
import ast
import struct
from pathlib import Path


def compile_catalogue(path):
    entries = {}
    key = value = None
    current = None
    def finish():
        if key is not None and value is not None:
            entries[key] = value
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            finish()
            key, value, current = ast.literal_eval(line[6:]), None, "key"
        elif line.startswith("msgstr "):
            value, current = ast.literal_eval(line[7:]), "value"
        elif line.startswith('"') and current:
            if current == "key":
                key += ast.literal_eval(line)
            else:
                value += ast.literal_eval(line)
        else:
            raise ValueError(f"Unsupported gettext syntax in {path}: {line}")
    finish()
    keys = sorted(entries)
    size = len(keys)
    offset = 28 + 16 * size
    ids = b""; values = b""; id_table = []; value_table = []
    for key in keys:
        raw = key.encode("utf-8")
        id_table.append((len(raw), offset + len(ids)))
        ids += raw + b"\0"
    for key in keys:
        raw = entries[key].encode("utf-8")
        value_table.append((len(raw), offset + len(ids) + len(values)))
        values += raw + b"\0"
    binary = struct.pack("<7I", 0x950412de, 0, size, 28, 28 + 8 * size, 0, 0)
    binary += b"".join(struct.pack("<2I", *row) for row in id_table + value_table) + ids + values
    path.with_suffix(".mo").write_bytes(binary)
    print(f"Compiled {path.name}: {size - 1} messages")


if __name__ == "__main__":
    for catalogue in (Path(__file__).resolve().parent.parent / "locale").glob("*/LC_MESSAGES/django.po"):
        compile_catalogue(catalogue)
