import hashlib


class CalculateChecksum:
    @classmethod
    def execute(cls, file_path: str) -> str:
        hash_function = getattr(hashlib, "sha256")()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_function.update(chunk)

        return hash_function.hexdigest()
