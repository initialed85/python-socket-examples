import os
import socket
from threading import Event

from socket_example.common import get_stdout_logger

_HOST = os.getenv("HOST", "localhost")


class TCPClient(object):
    def __init__(self):
        self._logger = get_stdout_logger(self)

        # create a TCP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # stop that pesky "socket already in use" error on repeated restarts
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # without this things block forever- this way we can interrupt threads etc
        self._socket.settimeout(1)

        # connect the socket
        self._socket.connect((_HOST, 12345))

        self._logger.debug(f"{repr(self._socket)} created and connected")

        self._stop_event = Event()

    def loop(self):
        data_buffer = b""

        pings_sent = 0
        pongs_received = 0

        # send pings as fast as possible
        while not self._stop_event.is_set():
            if pings_sent % 1000 == 0 or pongs_received % 1000 == 0:
                self._logger.debug(
                    f"pings_sent={pings_sent}, pongs_received={pongs_received}"
                )

            try:
                # try to send our ping
                self._socket.send(b"ping\n")

                pings_sent += 1

                while not self._stop_event.is_set():
                    # try to read 1 byte from socket- might timeout or error
                    data = self._socket.recv(1)

                    # an empty response means the socket is dead
                    if not data:
                        raise ValueError("received data empty")

                    # add our byte to the buffer
                    data_buffer += data

                    # buffer not yet ready
                    if len(data_buffer) < 5:
                        continue

                    # if the buffer is insane, throw it all away
                    if data_buffer != b"pong\n":
                        self._logger.error("insane response")
                        self._socket.send(b"error: unsupported response")
                        break

                    pongs_received += 1

                    # finish with this response
                    break

                # and clear the buffer
                data_buffer = b""
            except socket.timeout:
                continue
            except (socket.error, ValueError) as e:
                self._logger.error(repr(e))
                break

        self._logger.debug(f"loop exited")

        try:
            self._socket.close()
        except Exception:
            pass

        self._logger.debug(f"socket closed")

    def shutdown(self):
        self._socket.close()


def main():
    c = TCPClient()
    try:
        c.loop()
    except KeyboardInterrupt:
        pass
    finally:
        c.shutdown()


if __name__ == "__main__":
    main()
