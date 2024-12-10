from dataclasses import dataclass
from typing import Dict


@dataclass
class HTTPRequest:
    method: str = None
    endpoint: str = None
    query_strings: Dict[str, str] = None
    http_version: str = None
    host: str = None
    user_agent: str = None
    accept: str = None
    accept_language: str = None
    accept_encoding: str = None
    content_type: str = None
    content_length: str = None
    origin: str = None
    connection: str = None
    referer: str = None
    upgrade_insecure_requests: str = None
    sec_fetch_dest: str = None
    sec_fetch_mode: str = None
    sec_fetch_site: str = None
    sec_fetch_user: str = None
    priority: str = None
