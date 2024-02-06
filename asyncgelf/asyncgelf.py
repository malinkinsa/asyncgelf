import asyncio
import httpx
import json
import math
import os
import re
import socket
import ssl
import struct
import zlib

from typing import Optional, Dict


class GelfBase(object):
    def __init__(
            self,
            host: str,
            port: Optional[int] = 12201,
            gelf_version: Optional[str] = 1.1,
            level: Optional[str] = 1,
            scheme: Optional[str] = 'http',
            tls: Optional = None,
            compress: Optional[bool] = False,
            compress_level: Optional[int] = 1,
            debug: Optional[bool] = False,
            additional_field: Optional[Dict] = None,
            dns_resolve: Optional[bool] = False,
    ):
        """
        :param host: graylog server address
        :param port: graylog input port
        :param gelf_version: GELF spec version
        :param level: the level equal to the standard syslog levels
        :param scheme: HTTP Scheme for GELF HTTP input only
        :param tls: Path to custom (self-signed) certificate in pem format
        :param compress: compress message before sending it to the server or not
        :param compress_level: set compression level: available from 1 (BEST_SPEED) to 9 (BEST_COMPRESSION)
        :param debug: additional information in error log
        :param additional_field: dictionary with additional fields which will be added to every gelf message
        :param dns_resolve: If enabled - Variable host will be checked to existence DNS as parameter, and if dns is
            found, than on initialization will resolve to ip and variable will be updated. By default, UDP handler gets
            resolved by DNS on every log message. See more: https://github.com/python/cpython/issues/91305
        """

        self.host = host
        self.port = port
        self.gelf_version = gelf_version
        self.domain = socket.getfqdn()
        self.level = level
        self.scheme = scheme
        self.compress = compress
        self.compress_level = compress_level
        self.tls = tls
        self.debug = debug
        self.additional_field = additional_field
        self.dns_resolve = dns_resolve

        """
        Gelf compliance checks:
            - All keys must start with underscore (_) prefix;
            - _id can't be additional field;
            - Allowed characters in field names are any word character (letter, number, underscore), dashes and dots.
        """
        if self.additional_field:
            prefix_pattern = re.compile(r'^_')
            character_pattern = re.compile(r'^[\w\.\-]*$')
            id_pattern = re.compile(r'^_id\b')

            for k, v in self.additional_field.items():
                if prefix_pattern.search(k) is None:
                    exit('Error. Allowed only names started with underscore (_)')

                if character_pattern.search(k) is None:
                    exit('Error. One or more additional fields contain unsupported character. '
                         'Allowed characters in field names are any word character (letter, number, underscore), '
                         'dashes and dots.')

                if id_pattern.search(k):
                    exit("Error. Don't allowed to send _id as additional field.")

        """
        If dns_resolve = True. 
        Checking the self.host variable for presence DNS name. If found - dns recorde be resolved to ip and override in 
        self.host 
        """
        if self.dns_resolve:
            hostname_pattern = re.compile(
                r'^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$'
            )

            if hostname_pattern.search(self.host):
                self.host = socket.gethostbyname(self.host)

    def make(self, message, timestamp: Optional = None):
        """
        Transforms each message into GELF
        :param message: input message
        :param timestamp: event timestamp in the format: seconds since UNIX epoch with optional decimal places for
        milliseconds
        :return: a dictionary representing a GELF log
        """
        gelf_message = {
            'version': self.gelf_version,
            'host': self.domain,
            'short_message': json.dumps(message),
            'level': self.level,
        }

        if self.additional_field:
            for k, v in self.additional_field.items():
                gelf_message.update({k: v})

        if timestamp:
            timestamp_pattern = r"^\d+(\.\d+)?$"
            if re.match(timestamp_pattern, str(timestamp)):
                gelf_message.update({'timestamp': timestamp})

        return gelf_message


class GelfTcp(GelfBase):
    async def tcp_handler(self, message, timestamp: Optional = None):
        """
        tcp handler for send logs to Graylog Input with type: gelf tcp
        :param message: message to send, can be list, str, dict
        :param timestamp: event timestamp in the format: seconds since UNIX epoch with optional decimal places for
        milliseconds
        :return: Exception
        """
        messages = []
        """
        Input type checking
        """
        if type(message) is not list:
            messages.append(message)

        else:
            messages = message

        try:
            if self.tls:
                ssl_contex = ssl.create_default_context()
                ssl_contex.load_verify_locations(cafile=self.tls)
                stream_reader, stream_writer = await asyncio.open_connection(
                    self.host, self.port, ssl=ssl_contex,
                )

            else:
                stream_reader, stream_writer = await asyncio.open_connection(
                    self.host, self.port,
                )

        except Exception as e:
            if self.debug:
                return f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"

            return getattr(e, 'message', repr(e))

        for message in messages:
            gelf_message = GelfBase.make(self, message, timestamp)
            """ Transforming GELF dictionary into bytes """
            bytes_msg = json.dumps(gelf_message).encode('utf-8')

            if self.compress:
                bytes_msg = zlib.compress(bytes_msg, level=self.compress_level)
            """ 
            if you send the message over tcp, it should always be null terminated or the input will reject it 
            """
            stream_writer.write(bytes_msg + b'\x00')

        stream_writer.close()


class GelfHttp(GelfBase):
    async def http_handler(self, message, timestamp: Optional = None):
        """
        http handler for send logs to Graylog Input with type: gelf http
        :param message: input message
        :param timestamp: event timestamp in the format: seconds since UNIX epoch with optional decimal places for
        milliseconds
        :return: http status code
        """
        header = {
            'Content-Type': 'application/json',
        }

        if self.compress:
            header.update({'Content-Encoding': 'gzip,deflate'})

        gelf_message = GelfBase.make(self, message, timestamp)

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
    async def udp_handler(self, message, timestamp: Optional = None):
        """
        UDP handler for send logs to Graylog Input with type: gelf udp
        :param message: input message
        :param timestamp: event timestamp in the format: seconds since UNIX epoch with optional decimal places for
        milliseconds
        :return: error in next case: message size more than 1048576 bytes
        """
        """
        Declaring limits for GELF messages
        """
        max_chunk_size = 8192
        max_chunk_count = 128

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        gelf_message = GelfBase.make(self, message, timestamp)
        bytes_msg = json.dumps(gelf_message).encode('utf-8')

        if self.compress:
            bytes_msg = zlib.compress(bytes_msg, level=self.compress_level)
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
