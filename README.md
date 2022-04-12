# AsyncGELF
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/malinkinsa/asyncgelf.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/malinkinsa/asyncgelf/context:python)
![PyPI - Downloads](https://img.shields.io/pypi/dm/asyncgelf)
![PyPI](https://img.shields.io/pypi/v/asyncgelf)

Async python logging handlers that send messages in the Graylog Extended Log Format (GELF).

- [AsyncGELF](#asyncgelf)
  - [List of ready to run GELF handlers](#list-of-ready-to-run-gelf-handlers)
  - [Get AsyncGELF](#get-asyncgelf)
  - [Usage](#usage)
    - [GELF TCP](#gelf-tcp)
    - [GELF HTTP](#gelf-http)
    - [Available params](#available-params)

## List of ready to run GELF handlers
- TCP (with and without TLS);
- HTTP (with and without TLS);

## Get AsyncGELF
```python
pip install asyncgelf
```

## Usage

### GELF TCP

```python
import asyncio
import asyncgelf

async def main(message):
    handler = asyncgelf.GelfTcp(
        host='127.0.0.1',
    )

    await handler.tcp_handler(message)

asyncio.run(main(message))
```

### GELF HTTP 

```python
import asyncio
import asyncgelf

async def main(message):
    handler = asyncgelf.GelfHttp(
        host='127.0.0.1',
    )

    await handler.http_handler(message)

asyncio.run(main(message))
```

### Available params
- ```host``` Requaried | Graylog server address;
- ```port``` Optional | Graylog input port (default: 12201);
- ```gelf_version``` Optional | GELF spec version (default: 1.1)
- ```level``` Optional | The level equal to the standard syslog levels (default: 1);
- ```scheme``` Optional | HTTP Scheme <i>for GELF HTTP input only</i> (default: http);
- ```tls``` Optional | Path to custom (self-signed) certificate in pem format (default: None)
- ```compress``` Optional | Compress message before sending it to the server or not <i>for GELF HTTP input only</i> (default: False)
- ```debug``` Optional | Additional information in error log (default: False)