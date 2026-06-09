from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    hash_obj = hashlib.new(algorithm)
    with Path(file_path).open("rb") as fp:
        while True:
            chunk = fp.read(8 * 1024 * 1024)
            if not chunk:
                break
            hash_obj.update(chunk)
    return hash_obj.hexdigest()
