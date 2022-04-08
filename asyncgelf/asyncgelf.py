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
            scheme: Optional[str] = 'http',
            compress: Optional = False,
    ):
        """
        :param host: graylog server address
        :param port: graylog input port
        :param gelf_version: GELF spec version
        :param level: the level equal to the standard syslog levels
        :param scheme: HTTP Scheme for GELF HTTP input only
        :param compress: compress message before sending it to the server or not
        """

        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()
        self.level = level
        self.scheme = scheme
        self.compress = compress

    def make(self, message):
        """
        Transforms each message into GELF
        :param message: input message
        :return: a dictionary representing a GELF log
        """
        gelf_message = {
            'version': self.gelf_version,
            'host': self.domain,
            'short_message': json.dumps(message),
            'level': self.level,
        }
        return gelf_message


class GelfTcp(GelfBase):
    async def tcp_handler(self, massage):
        """
        tcp handler for send logs to Graylog Input with type: gelf tcp
        :param massage: input message
        :return:
        """
        gelf_message = GelfBase.make(self, massage)
        """ Transforming GELF dictionary into bytes """
        bytes_msg = json.dumps(gelf_message).encode('utf-8')

        stream_reader, stream_writer = await asyncio.open_connection(
            self.host, self.port
        )

        """ if you send the message over tcp, it should always be null terminated or the input will reject it """
        stream_writer.write(bytes_msg + b'\x00')
        stream_writer.close()


class GelfHttp(GelfBase):
    async def http_handler(self, message):
        """
        http handler for send logs to Graylog Input with type: gelf http
        :param message: input message
        :return: http status code
        """
        header = {
            'Content-Type': 'application/json',
        }

        if self.compress:
            header.update({'Content-Encoding': 'gzip,deflate'})

        gelf_message = GelfBase.make(self, message)
        gelf_endpoint = f'{self.scheme}://{self.host}:{self.port}/gelf'

        async with httpx.AsyncClient() as client:
            response = await client.post(
                gelf_endpoint,
                headers=header,
                data=json.dumps(gelf_message),
            )
            return response.status_code
