# python-socket-examples

This repo contains some very basic client-server examples for TCP and UDP sockets using the standard socket library for training purposes.

The example implements the following:

- TCP echo server
- TCP echo client
- UDP echo server
- UDP echo client

In all cases the protocol is as follows:

- Server expects `ping\n` requests and sends `pong\n` in response
    - Any other request results in a `error\n` response
- Client sends `ping\n` requests as fast as possible and expects `pong\n` in response
    - Any other response results in the Client exiting

## Prerequisites

- Python3.6+
- Probably a POSIX environment (no promises for Windows)

## Usage

**Monitoring**

```
sudo tcpdump -AvvvXeni any port 12345
```

**TCP server**

```
python -m socket_example.tcp_server
```

**TCP client**

```
python -m socket_example.tcp_client
```

**UDP server**

```
python -m socket_example.udp_server
```

**UDP client**

```
python -m socket_example.udp_client
```

You can run all of these concurrently and you can run as many Clients as you like.
