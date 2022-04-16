import asyncio
import httpx
import json
import math
import os
import socket
import ssl
import struct
import zlib

from typing import Optional


class GelfBase(object):
    def __init__(
            self,
            host: str,
            port: Optional[int] = 12201,
            gelf_version: Optional[str] = 1.1,
            level: Optional[str] = 1,
            scheme: Optional[str] = 'http',
            tls: Optional = None,
            compress: Optional = False,
            debug: Optional = False
    ):
        """
        :param host: graylog server address
        :param port: graylog input port
        :param gelf_version: GELF spec version
        :param level: the level equal to the standard syslog levels
        :param scheme: HTTP Scheme for GELF HTTP input only
        :param tls: Path to custom (self-signed) certificate in pem format
        :param compress: compress message before sending it to the server or not
        :param debug: additional information in error log
        """

        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()
        self.level = level
        self.scheme = scheme
        self.compress = compress
        self.tls = tls
        self.debug = debug

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
        :return: Exception
        """
        gelf_message = GelfBase.make(self, massage)
        """ Transforming GELF dictionary into bytes """
        bytes_msg = json.dumps(gelf_message).encode('utf-8')

        if self.compress:
            bytes_msg = zlib.compress(bytes_msg, level=1)

        if self.tls:
            ssl_contex = ssl.create_default_context()
            ssl_contex.load_verify_locations(cafile=self.tls)

            try:
                stream_reader, stream_writer = await asyncio.open_connection(
                    self.host,
                    self.port,
                    ssl=ssl_contex,
                )

                """ 
                if you send the message over tcp, it should always be null terminated or the input will reject it 
                """
                stream_writer.write(bytes_msg + b'\x00')
                stream_writer.close()

            except Exception as e:
                if self.debug:
                    return f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"

                return getattr(e, 'message', repr(e))

        try:
            stream_reader, stream_writer = await asyncio.open_connection(
                self.host,
                self.port,
            )

            """ 
            if you send the message over tcp, it should always be null terminated or the input will reject it 
            """
            stream_writer.write(bytes_msg + b'\x00')
            stream_writer.close()

        except Exception as e:
            if self.debug:
                return f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"

            return getattr(e, 'message', repr(e))


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

        if self.tls:
            ssl_contex = ssl.create_default_context()
            ssl_contex.load_verify_locations(cafile=self.tls)

            gelf_endpoint = f'https://{self.host}:{self.port}/gelf'

            try:
                async with httpx.AsyncClient(verify=ssl_contex) as client:
                    response = await client.post(
                        gelf_endpoint,
                        headers=header,
                        data=json.dumps(gelf_message),
                    )

                    return response.status_code

            except Exception as e:
                if self.debug:
                    return f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"

                return getattr(e, 'message', repr(e))

        gelf_endpoint = f'{self.scheme}://{self.host}:{self.port}/gelf'

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    gelf_endpoint,
                    headers=header,
                    data=json.dumps(gelf_message),
                )

                return response.status_code

        except Exception as e:
            if self.debug:
                return f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"

            return getattr(e, 'message', repr(e))


class GelfUdp(GelfBase):
    async def udp_handler(self, message):
        """
        UDP handler for send logs to Graylog Input with type: gelf udp
        :param message: input message
        :return: Message send error in next case: message size more than 1048576 bytes
        """
        """
        Declaring limits for GELF messages
        """
        max_chunk_size = 8192
        max_chunk_count = 128

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        gelf_message = GelfBase.make(self, message)
        bytes_msg = json.dumps(gelf_message).encode('utf-8')

        if self.compress:
            bytes_msg = zlib.compress(bytes_msg, level=1)
        """
        Checking the message size. 
        """
        if len(bytes_msg) > max_chunk_size:
            total_chunks = int(math.ceil(len(bytes_msg) / max_chunk_size))

            if total_chunks > max_chunk_count:
                return "Error. Your message couldn't be sent because it's too large."

            chunks = [bytes(bytes_msg)[i: i + max_chunk_size] for i in range(0, len(bytes(bytes_msg)), max_chunk_size)]

            async for i in self.make_gelf_chunks(chunks, total_chunks):
                client_socket.sendto(i, (
                    self.host,
                    self.port
                ))

        client_socket.sendto(bytes_msg, (
            self.host,
            self.port
        ))

    async def make_gelf_chunks(self, chunks, total_chunks):
        """
        Each chunk is padded with overhead to match the GELF specification.
        :param chunks: Chunked gelf_message
        :param total_chunks: The total number of chunks a GELF message requires to send
        :return:
        """
        message_id = os.urandom(8)

        for chunk_index, chunk in enumerate(chunks):
            yield b''.join((
                b'\0x1e\0x0f',
                message_id,
                struct.pack('b', chunk_index),
                struct.pack('b', total_chunks),
                chunk
            ))
