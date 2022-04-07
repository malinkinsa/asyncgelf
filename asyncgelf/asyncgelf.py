import asyncio
import json
import socket

from typing import Dict, Optional


class GelfBase(object):
    def __init__(self, host: str, port: Optional[int] = 12201, gelf_version: Optional[str] = 1.1,
                 level: Optional[str] = 1):
        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()
        self.level = level

    def make(self, payload):
        msg = {
            'version': self.gelf_version,
            'host': self.domain,
            'short_message': json.dumps(payload),
            'level': self.level,
        }
        return msg


class GelfTcp(GelfBase):
    async def tcp_handler(self, payload: Dict):
        msg = GelfBase.make(self, payload)

        gelf_message = json.dumps(msg).encode('utf-8')

        stream_reader, stream_writer = await asyncio.open_connection(
            self.host, self.port
        )

        stream_writer.write(gelf_message + b'\x00')
        stream_writer.close()
