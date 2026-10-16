"""Context-scoped network guard for the long-lived, threaded UI server process.

The sealed ``no_network()`` (src/experiments/h2_evaluation_offline.py, lines
123-129) swaps ``socket.socket.connect``, ``connect_ex`` and
``socket.create_connection`` for the whole process. In the threaded server that:

1. blocks every other thread while one offline check runs (a GET preflight
   made the paid Radar worker fail: incident 2026-10-12 02:59 BRT), and
2. can stay installed forever when two checks overlap in different threads,
   because each ``patch.object`` restores whatever it saw on entry.

``install()`` puts one permanent dispatcher on those three attributes. It
refuses exactly what the sealed guard refuses, with the same message, but only
when the *current context* is inside ``no_network()`` below; it then rebinds
every loaded ``no_network`` name (including the sealed module's) to it.
Context variables follow ``asyncio`` tasks and ``asyncio.to_thread``; plain
threads start outside the offline scope, so a worker is never blocked by a
check running in another request.

``qualified()`` is what the server reports and what paid Radar commands require:
all three attributes carry the dispatcher and no loaded module still holds the
sealed guard. Ceiling: on interpreters where ``threading.Thread`` inherits the
caller's context (free-threaded 3.14 default), a thread started *inside* an
offline scope would inherit it; no worker is started from inside one today.
"""

import _socket
import contextvars
import ipaddress
import socket
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.experiments import h2_evaluation_offline as sealed

MESSAGE = "offline qualification forbids network"
SEALED = sealed.no_network
_OFFLINE = contextvars.ContextVar("hfl_offline_scope", default=False)


@contextmanager
def no_network():
    token = _OFFLINE.set(True)
    try:
        yield
    finally:
        _OFFLINE.reset(token)


def offline():
    return _OFFLINE.get()


def _local(sock, address):
    # Same rule as the sealed guard: loopback and AF_UNIX (asyncio self-pipe).
    if isinstance(address, tuple):
        try:
            return ipaddress.ip_address(address[0]).is_loopback
        except ValueError:
            return False
    return sock.family == getattr(socket, "AF_UNIX", object())


def _genuine():
    """True when the three attributes are the interpreter's own (no patch active)."""
    return (
        socket.socket.connect is _socket.socket.connect
        and socket.socket.connect_ex is _socket.socket.connect_ex
        and getattr(socket.create_connection, "__module__", None) == "socket"
        and getattr(socket.create_connection, "__qualname__", None) == "create_connection"
    )


def qualified():
    """Scoped guard on all three attributes and no loaded module left on the sealed one."""
    # ``is True``: a MagicMock (the sealed guard) answers any attribute truthily.
    installed = all(
        getattr(value, "_hfl_scoped", False) is True
        for value in (
            socket.socket.connect,
            socket.socket.connect_ex,
            socket.create_connection,
        )
    )
    return installed and not any(
        getattr(module, "no_network", None) is SEALED
        for module in list(sys.modules.values())
    )


def install():
    """Idempotent; call once at server/CLI startup, before serving requests."""
    if getattr(socket.create_connection, "_hfl_scoped", False) is not True:
        if not _genuine():
            # A sealed guard (or any patch) is active right now: capturing it as the
            # "original" would make the block permanent. Refuse; restart the process.
            raise RuntimeError("network_patch_active_at_install")
        connect, connect_ex, create = (
            socket.socket.connect,
            socket.socket.connect_ex,
            socket.create_connection,
        )

        def guard(original):
            def call(sock, address):
                if _OFFLINE.get() and not _local(sock, address):
                    raise RuntimeError(MESSAGE)
                return original(sock, address)

            call._hfl_scoped = True
            return call

        def create_connection(*args, **kwargs):
            if _OFFLINE.get():  # the sealed guard refuses every create_connection
                raise RuntimeError(MESSAGE)
            return create(*args, **kwargs)

        create_connection._hfl_scoped = True
        socket.socket.connect, socket.socket.connect_ex = (
            guard(connect),
            guard(connect_ex),
        )
        socket.create_connection = create_connection
    # ponytail: rebinds module globals named no_network; a module imported later
    # with ``from ... import no_network`` gets this one because the sealed module's
    # attribute is rebound too. Ceiling: a reference captured elsewhere (closure,
    # default argument) would still reach the sealed guard; none exists today.
    for module in list(sys.modules.values()):
        try:
            if getattr(module, "no_network", None) is SEALED:
                module.no_network = no_network
        except Exception:  # lazy or odd modules may refuse getattr
            continue
