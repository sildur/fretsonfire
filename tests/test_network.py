"""Tests for the basic network handshake."""
from __future__ import annotations

from contextlib import suppress

import pytest

from src.fretsonfire import Network


class DummyConnection(Network.Connection):
    def handlePacket(self, packet):
        if isinstance(packet, bytes):
            packet = packet.decode("utf-8")
        self.packet = packet


class DummyServer(Network.Server):
    def createConnection(self, sock):
        return DummyConnection(sock)


def test_handshake_roundtrip():
    server = DummyServer(port=0)
    port = server.socket.getsockname()[1]
    client = DummyConnection()

    try:
        client.connect("localhost", port)
        client.sendPacket("moikka")

        for _ in range(200):
            Network.communicate()
            if server.clients:
                break
        else:
            pytest.fail("Client did not register with server")

        client_conn = next(iter(server.clients.values()))

        for _ in range(200):
            Network.communicate()
            if getattr(client_conn, "packet", None) == "moikka":
                break
        else:
            pytest.fail("Client did not receive echoed packet")

        assert client_conn.packet == "moikka"
        assert client_conn.id == 1
    finally:
        with suppress(Exception):
            client.close()
        Network.shutdown()
