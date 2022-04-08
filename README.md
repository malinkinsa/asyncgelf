# AsyncGELF

Async python logging handlers that send messages in the Graylog Extended Log Format (GELF).

- [AsyncGELF](#asyncgelf)
  - [List of ready to run GELF handlers](#list-of-ready-to-run-gelf-handlers)
  - [Get AsyncGELF](#get-asyncgelf)
  - [Usage](#usage)
    - [GELF TCP](#gelf-tcp)
    - [GELF HTTP](#gelf-http)
    - [Available params](#available-params)

## List of ready to run GELF handlers
- TCP (without TLS);
- HTTP;  

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
- ```scheme``` Optional | HTTP Scheme for GELF HTTP input only (default: http);