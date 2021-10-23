import socket
from threading import Event, Thread
from typing import List

from socket_example.common import get_stdout_logger


class TCPServerClient(object):
    def __init__(self, client_socket, client_host, client_port):
        self._logger = get_stdout_logger(self, f"{client_host}:{client_port}")

        self._socket: socket.socket = client_socket
        self._host = client_host
        self._port = client_port

        # without this things block forever- this way we can interrupt threads etc
        self._socket.settimeout(1)

        self._logger.debug(f"{repr(self._socket)} given")

        self._stop_event = Event()

        # so we can service requests for this client in the background
        self._thread = Thread(target=self._loop)
        self._thread.start()

        self._logger.debug(f"loop started")

    def is_stopped(self):
        stopped = self._stop_event.is_set()
        if stopped:
            self._thread.join()

        return stopped

    def shutdown(self):
        self._stop_event.set()

    def _loop(self):
        data_buffer = b""

        pings_received = 0
        pongs_sent = 0

        while not self._stop_event.is_set():
            if pings_received % 1000 == 0 or pongs_sent % 1000 == 0:
                self._logger.debug(
                    f"pings_received={pings_received}, pongs_sent={pongs_sent}"
                )

            try:
                # try to read 1 byte from socket- might timeout or error
                data = self._socket.recv(1)

                # an empty response means the socket is dead
                if not data:
                    break

                # add our byte to the buffer
                data_buffer += data

                # buffer not yet ready
                if len(data_buffer) < 5:
                    continue

                # if the buffer is insane, throw away this client
                if data_buffer != b"ping\n":
                    self._logger.error("insane request")
                    self._socket.send(b"error\n")
                    break

                pings_received += 1

                # send our pong
                self._socket.send(b"pong\n")

                # and clear the buffer
                data_buffer = b""

                pongs_sent += 1
            except socket.timeout:  # a timeout is okay
                continue
            except socket.error as e:  # an error can't be recovered from
                self._logger.error(repr(e))
                break

        self._logger.debug(f"loop exited")

        try:
            self._socket.close()
        except Exception:
            pass

        self._logger.debug(f"socket closed")


class TCPServer(object):
    def __init__(self):
        self._logger = get_stdout_logger(self)

        self._stop_event = Event()

        self._server_clients: List[TCPServerClient] = []

        # create a TCP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # stop that pesky "socket already in use" error on repeated restarts
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # without this things block forever- this way we can interrupt threads etc
        self._socket.settimeout(1)

        # bind to all interfaces, port 12345
        self._socket.bind(("", 12345))

        # size of the "waiting room"
        self._socket.listen(0)

        self._logger.debug(f"{repr(self._socket)} created, bound and listening")

    def loop(self):
        self._logger.debug(f"waiting for connections...")

        while not self._stop_event.is_set():
            # prune anything dead
            self._server_clients = [
                x for x in self._server_clients if not x.is_stopped()
            ]

            # this call will block until somebody connects
            try:
                client_socket, (client_host, client_port) = self._socket.accept()
            except socket.timeout:
                continue

            # something to handle the lifecycle of our client connection
            server_client = TCPServerClient(
                client_socket=client_socket,
                client_host=client_host,
                client_port=client_port,
            )

            self._logger.debug(
                f"{repr(client_host)}:{repr(client_port)} connected, {repr(server_client)} created"
            )

            self._server_clients.append(server_client)

    def shutdown(self):
        for server_client in self._server_clients:
            server_client.shutdown()

        self._socket.close()


def main():
    s = TCPServer()
    try:
        s.loop()
    except KeyboardInterrupt:
        pass
    finally:
        s.shutdown()


if __name__ == "__main__":
    main()
