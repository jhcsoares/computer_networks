from dataclasses import dataclass


@dataclass
class ClientRequest:
    file_name: str
    discarded_pkts: int
