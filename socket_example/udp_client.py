import os
import socket
from threading import Event

from socket_example.common import get_stdout_logger

_HOST = os.getenv("HOST", "localhost")


class UDPClient(object):
    def __init__(self):
        self._logger = get_stdout_logger(self)

        # create a UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # stop that pesky "socket already in use" error on repeated restarts
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # without this things block forever- this way we can interrupt threads etc
        self._socket.settimeout(1)

        self._logger.debug(f"{repr(self._socket)} created")

        self._stop_event = Event()

    def loop(self):
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
                self._socket.sendto(b"ping\n", (_HOST, 12345))

                pings_sent += 1

                data, (server_host, server_port) = self._socket.recvfrom(65536)
                if not data:
                    break

                # if the buffer is insane, throw it all away
                if data != b"pong\n":
                    self._logger.error("insane response")
                    self._socket.sendto(
                        b"error: unsupported response", (server_host, server_port)
                    )
                    break

                pongs_received += 1
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
    c = UDPClient()
    try:
        c.loop()
    except KeyboardInterrupt:
        pass
    finally:
        c.shutdown()


if __name__ == "__main__":
    main()
