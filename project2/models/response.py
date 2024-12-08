from dataclasses import asdict, dataclass

import json


@dataclass
class Response:
    status: int
    message: str

    def encode(self) -> bytes:
        return json.dumps(asdict(self), indent=4).encode("utf-8")
