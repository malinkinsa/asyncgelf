import asyncio
import json
import httpx
import socket

from typing import Optional


class GelfBase(object):
    def __init__(
            self,
            host: str,
            port: Optional[int] = 12201,
            gelf_version: Optional[str] = 1.1,
            level: Optional[str] = 1,
            scheme: Optional[str] = 'http'
    ):

        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()
        self.level = level
        self.scheme = scheme

    def make(self, message):
        gelf_message = {
            'version': self.gelf_version,
            'host': self.domain,
            'short_message': json.dumps(message),
            'level': self.level,
        }
        return gelf_message


class GelfTcp(GelfBase):
    async def tcp_handler(self, massage):
        gelf_message = GelfBase.make(self, massage)

        bytes_msg = json.dumps(gelf_message).encode('utf-8')

        stream_reader, stream_writer = await asyncio.open_connection(
            self.host, self.port
        )

        stream_writer.write(bytes_msg + b'\x00')
        stream_writer.close()


class GelfHttp(GelfBase):
    async def http_handler(self, message):
        header = {
            'Content-Type': 'application/json',
            'Content-Encoding': 'gzip,deflate',
        }
        gelf_message = GelfBase.make(self, message)
        gelf_endpoint = f'{self.scheme}://{self.host}:{self.port}/gelf'

        async with httpx.AsyncClient() as client:
            response = await client.post(
                gelf_endpoint,
                headers=header,
                data=json.dumps(gelf_message),
            )
            return response.status_code
