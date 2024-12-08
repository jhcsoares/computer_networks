from dataclasses import asdict, dataclass

import json


@dataclass
class FileData:
    checksum: str
    size: int

    def encode(self) -> bytes:
        return json.dumps(asdict(self), indent=4).encode("utf-8")

    def serialize(self) -> str:
        return json.dumps(asdict(self), indent=4)
