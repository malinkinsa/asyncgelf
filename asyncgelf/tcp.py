import asyncio
import json
import socket

from typing import Dict, Optional


class GelfTcp:
    def __init__(self, host: str, port: Optional[int] = 12201, gelf_version: Optional[str] = 1.1):
        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()

    async def send_data(self, payload: Dict, level: Optional[str] = 1):
        gelf_message = {
            'version': self.gelf_version,
            'host': self.domain,
            'short_message': json.dumps(payload),
            'level': level,
        }

        gelf_message = json.dumps(gelf_message).encode('utf-8')

        reader, writer = await asyncio.open_connection(
            self.host, self.port
        )

        writer.write(gelf_message + b'\x00')
        writer.close()
