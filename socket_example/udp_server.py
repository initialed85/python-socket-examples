import socket
from threading import Event

from socket_example.common import get_stdout_logger


class UDPServer(object):
    def __init__(self):
        self._logger = get_stdout_logger(self)

        self._stop_event = Event()

        # create a UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # stop that pesky "socket already in use" error on repeated restarts
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # without this things block forever- this way we can interrupt threads etc
        self._socket.settimeout(1)

        # bind to all interfaces, port 12345
        self._socket.bind(("", 12345))

    def loop(self):
        self._logger.debug(f"waiting for connections...")

        pings_received = 0
        pongs_sent = 0

        while not self._stop_event.is_set():
            if pings_received % 1000 == 0 or pongs_sent % 1000 == 0:
                self._logger.debug(
                    f"pings_received={pings_received}, pongs_sent={pongs_sent}"
                )

            try:
                data, (client_host, client_port) = self._socket.recvfrom(65536)

                # if the buffer is insane, ignore this client
                if data != b"ping\n":
                    self._logger.error("insane request")
                    self._socket.sendto(b"error\n", (client_host, client_port))
                    continue

                pings_received += 1

                self._socket.sendto(b"pong\n", (client_host, client_port))

                pongs_sent += 1
            except socket.timeout:
                continue
            except socket.error as e:
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
    s = UDPServer()
    try:
        s.loop()
    except KeyboardInterrupt:
        pass
    finally:
        s.shutdown()


if __name__ == "__main__":
    main()
