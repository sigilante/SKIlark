"""The host of SKIlark's I/O words.

The kernel has no effects.  An I/O word stops the run: ``RIO n s q``, the
word (``joy.IO``, by number), the stack, and the rest of the program.  The
host does what the word does, as the reference's ``src/<name>.c`` does it,
and runs ``q`` on the stack its answer leaves: a pushed value, or nothing
pushed and some output written.  So a run is a sequence of pure
reductions, and a host that answers the same way gives the same run.

:class:`Host` answers from what it is given (input text, arguments, an
environment, a clock), so tests and the reference model share one world;
:func:`live` gives one over this process's own.  Values travel as the
reference model's tagged tuples (``joyfile.value``), so ``put`` writes
what ``joyfile.write`` writes.

The run's fuel, where it has any, starts again after each answer: fuel is
SKIlark's bound on a run, not Joy's, and ``q`` is a datum where the fuel
is not.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import joy

Value = Tuple

#: what an answer is: ("stack", the stack term to run the rest on), or the
#: run's end: ("RErr",), ("RQuit",), or ("RAbort", the stack term)
Answer = Tuple


def factor_end(text: str, i: int) -> int:
    """Where the factor starting at ``text[i]`` ends: a list or set at its
    matching bracket, a string or character whole, anything else at the
    next space or bracket (scan.c's tokens)."""
    n, depth = len(text), 0
    while i < n:
        c = text[i]
        if c == '"':                                # a string, escapes and all
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif c == "'":                              # 'x, '\n or '\065
            i += 2
            if text[i - 1:i] == "\\":
                j = i + 2                           # at most three digits
                i += 1
                while i < n and i <= j and text[i - 1].isdigit() and text[i].isdigit():
                    i += 1
        elif c in "[{":
            depth += 1
            i += 1
        elif c in "]}":
            depth -= 1
            i += 1
        elif c.isspace():
            i += 1
        else:
            i += 1
            if depth == 0 and i < n and not (text[i].isspace() or text[i] in "[]{}"):
                continue
        if depth <= 0:
            return i
    return i


def _from_parse(t: Any) -> Value:
    """A parsed factor (``joy.parse``) as a value."""
    if isinstance(t, bool):
        return ("B", t)
    if isinstance(t, int):
        return ("N", t)
    if isinstance(t, list):
        return ("L", tuple(_from_parse(u) for u in t))
    if isinstance(t, tuple):
        if t[0] == "C":
            return ("C", t[1])
        if t[0] == "Z":
            return ("Z", tuple(sorted(t[1])))
        return ("T", tuple(t[1]))
    if t in ("true", "false"):
        return ("B", t == "true")
    return ("S", t)


class Host:
    """A world for the I/O words: ``stdin``'s text, which ``get`` reads a
    factor at a time; ``argv``, the interpreter's arguments, its name
    first; ``env``; and ``clock``, the milliseconds ``clock`` pushes.
    What the words write collects in ``out``."""

    def __init__(self, stdin: str = "", argv: Sequence[str] = ("joy",),
                 env: Optional[Dict[str, str]] = None,
                 clock: Callable[[], int] = lambda: 0):
        self.stdin, self.at = stdin, 0
        self.argv = list(argv)
        self.env = dict(env or {})
        self.clock = clock
        self.out: List[str] = []

    def text(self) -> str:
        return "".join(self.out)

    def write(self, s: str) -> None:
        self.out.append(s)

    # -------------------------------------------------------- the words

    def answer(self, run, code: int, stack) -> Answer:
        """The answer to the I/O word numbered ``code`` on ``stack``."""
        name = list(joy.IO)[code]
        return getattr(self, "w_" + name)(run, stack)

    def w_put(self, run, s):            # put.c: writefactor
        got = run.pop(s, 1)
        if got is None:
            return ("RErr",)
        (x,), t = got
        from .joyfile import write
        self.write(write(x))
        return ("stack", t)

    def w_putch(self, run, s):          # putch.c: NUMERICTYPE, printf %c
        got = run.pop(s, 1)
        if got is None or got[0][0][0] not in ("N", "C"):
            return ("RErr",)
        self.write(chr(got[0][0][1] & 0xFF))
        return ("stack", got[1])

    def w_putchars(self, run, s):       # putchars.c: STRING, printf %s
        got = run.pop(s, 1)
        if got is None or got[0][0][0] != "T":
            return ("RErr",)
        self.write("".join(map(chr, got[0][0][1])))
        return ("stack", got[1])

    def w_get(self, run, s):            # get.c: readfactor from the input
        v = self.read_factor()
        if v is None:
            return ("RErr",)
        return ("stack", run.push(s, v))

    def read_factor(self) -> Optional[Value]:
        """The next factor of the input, or None at its end or where it
        does not read."""
        text, i = self.stdin, self.at
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return None
        j = factor_end(text, i)
        self.at = j
        try:
            parsed = joy.parse(text[i:j])
        except (ValueError, IndexError):
            return None
        return _from_parse(parsed[0]) if len(parsed) == 1 else None

    def w_argc(self, run, s):           # argc.c
        return ("stack", run.push(s, ("N", len(self.argv))))

    def w_argv(self, run, s):           # argv.c: a list of strings
        return ("stack", run.push(s, ("L", tuple(("T", tuple(map(ord, a))) for a in self.argv))))

    def w_getenv(self, run, s):         # getenv.c: "" when unset
        got = run.pop(s, 1)
        if got is None or got[0][0][0] != "T":
            return ("RErr",)
        value = self.env.get("".join(map(chr, got[0][0][1])), "")
        return ("stack", run.push(got[1], ("T", tuple(map(ord, value)))))

    def w_clock(self, run, s):          # clock.c: CPU milliseconds
        return ("stack", run.push(s, ("N", int(self.clock()))))

    def w_abort(self, run, s):          # abort.c: back to the main cycle
        return ("RAbort", s)

    def w_quit(self, run, s):           # quit.c: out of Joy
        return ("RQuit",)


def live(argv: Sequence[str] = ("joy",)) -> Host:
    """A host over this process: its standard input, read whole when
    ``get`` first asks, its environment, and its CPU clock."""
    start = time.process_time()

    class Live(Host):
        def read_factor(self):
            if self.stdin is None:
                self.stdin = sys.stdin.read()
            return Host.read_factor(self)

        def write(self, s):
            Host.write(self, s)
            sys.stdout.write(s)
            sys.stdout.flush()

    h = Live(argv=argv, env=dict(os.environ),
             clock=lambda: int((time.process_time() - start) * 1000))
    h.stdin = None  # type: ignore[assignment]
    return h
