"""Joy files, as the reference reads and runs them (Wodan58/Joy's scan.c,
main.c, print.c): ``(* *)`` and ``#`` comments, ``DEFINE`` (or ``LIBRA``)
blocks of ``name == body`` separated by ``;`` and ended by ``.``, and
terms each ended by ``.``.  Every term runs on the stack the terms before
it left, and after each the reference prints the top of the stack and
pops it (its default autoput, 1): ``run_file`` gives those lines.

SKIlark runs a program from the empty stack, so the k-th line comes from
the first k terms as one program, a pop after each but the last when the
stack is not empty: the same values, the earlier terms run again.  One
program for the whole file, its stack a list each term runs on by
``infra``, would be cheaper under sharing but not under the tests' copy
mode, which computes the list again at every term that looks at it.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import joy

#: what a term may begin with that the reference reads and SKIlark does not
UNSUPPORTED = ("HIDE", "IN", "END", "MODULE", "PRIVATE", "PUBLIC", "CONST", "INLINE")

#: the pop the reference's print makes, when there is a top to print
POP = "stack null [] [pop] branch"


class JoyFileError(ValueError):
    """A file the reader cannot take."""


def _strip(text: str) -> str:
    """The text without its comments, strings and characters kept whole."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':                                # a string, escapes and all
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1]); i = j + 1
        elif c == "'" and i + 1 < n:                # a character: 'x or '\n or '\065
            j = i + 2
            if text[i + 1] == "\\":
                j = i + 3
                while j < n and j < i + 5 and text[j].isdigit():
                    j += 1
            out.append(text[i:j]); i = j
        elif text.startswith("(*", i):
            j = text.find("*)", i + 2)
            if j < 0:
                raise JoyFileError("a comment (* with no *)")
            out.append(" "); i = j + 2
        elif c == "#":
            j = text.find("\n", i)
            out.append(" "); i = n if j < 0 else j
        else:
            out.append(c); i += 1
    return "".join(out)


def _split(text: str, stop: str) -> List[str]:
    """``text`` cut at each ``stop`` outside strings and characters."""
    parts, cur, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            cur.append(text[i:j + 1]); i = j + 1
        elif c == "'" and i + 1 < n:
            j = i + (3 if text[i + 1] == "\\" else 2)
            while text[i + 1] == "\\" and j < n and j < i + 5 and text[j].isdigit():
                j += 1
            cur.append(text[i:j]); i = j
        elif c == stop:
            parts.append("".join(cur)); cur = []; i += 1
        else:
            cur.append(c); i += 1
    parts.append("".join(cur))
    return parts


def read(text: str) -> List[Tuple[str, Any]]:
    """A file's items in order: ``("define", {name: body})`` or ``("term", text)``."""
    items: List[Tuple[str, Any]] = []
    chunks = _split(_strip(text), ".")
    if chunks[-1].strip():
        raise JoyFileError(f"a term with no period: {chunks[-1].strip()!r}")
    for chunk in chunks[:-1]:
        body = chunk.strip()
        if not body:                                # an empty term: the top is printed
            items.append(("term", ""))
            continue
        head = body.split(None, 1)[0]
        if head in UNSUPPORTED:
            raise JoyFileError(f"{head} is the reference's and not SKIlark's")
        if head in ("DEFINE", "LIBRA"):
            defs: Dict[str, str] = {}
            for d in _split(body[len(head):], ";"):
                if not d.strip():
                    continue
                if "==" not in d:
                    raise JoyFileError(f"a definition with no ==: {d.strip()!r}")
                name, rhs = (x.strip() for x in d.split("==", 1))
                defs[name] = rhs
            items.append(("define", defs))
        else:
            items.append(("term", body))
    return items


# ---------------------------------------------------------- printing

def element(w: Any) -> Tuple:
    """An interpreted quotation's element as the reference's value."""
    if isinstance(w, str):
        return ("S", joy.NAMES[w])
    kind, v = w
    if kind == "Lit":
        return ("N", v)
    if kind == "Truth":
        return ("B", v)
    if kind == "Quote":
        return ("L", tuple(element(u) for u in v))
    if kind == "Def":
        return ("S", v)
    if kind == "Set":
        return ("Z", tuple(v))
    if kind == "Glyph":
        return ("C", v)
    if kind == "Text":
        return ("T", tuple(map(ord, v)) if isinstance(v, str) else tuple(v))
    raise ValueError(f"no value for {w!r}")


def value(v: Any) -> Tuple:
    """An interpreted stack item as the reference's value."""
    if isinstance(v, bool):
        return ("B", v)
    if isinstance(v, int):
        return ("N", v)
    if isinstance(v, list):
        return ("L", tuple(element(w) for w in v))
    kind, x = v
    if kind == "Sym":
        return ("S", x)
    if kind == "Char":
        return ("C", x)
    if kind == "Str":
        return ("T", tuple(map(ord, x)) if isinstance(x, str) else tuple(x))
    if kind == "Set":
        return ("Z", tuple(x))
    raise ValueError(f"no value for {v!r}")


def _char(c: int) -> str:
    """write.c writechar."""
    if 8 <= c <= 13:
        return "'\\" + "btnvfr"[c - 8]
    if c < 32 or c == 127 or c == 32:
        return f"'\\{c:03d}"
    return "'" + chr(c)


def _string(codes) -> str:
    """write.c writestring, quoted."""
    out = []
    for c in codes:
        if c == 34:
            out.append('\\"')
        elif 8 <= c <= 13:
            out.append("\\" + "btnvfr"[c - 8])
        elif c < 32 or c == 127:
            out.append(f"\\{c:03d}")
        else:
            out.append(chr(c))
    return '"' + "".join(out) + '"'


def write(v: Tuple) -> str:
    """write.c writefactor: a value as the reference prints it.  A set is
    its members, a list its elements, each space-separated."""
    kind, x = v
    if kind == "N":
        return str(x)
    if kind == "B":
        return "true" if x else "false"
    if kind == "C":
        return _char(x)
    if kind == "T":
        return _string(x)
    if kind == "S":
        return x
    if kind == "Z":
        members = [m for m in range(64) if x >> m & 1] if isinstance(x, int) else list(x)
        return "{" + " ".join(map(str, members)) + "}"
    if kind == "L":
        return "[" + " ".join(write(e) for e in x) + "]"
    raise ValueError(f"no writing of {v!r}")


# ---------------------------------------------------------- running

def programs(text: str) -> Tuple[Dict[str, str], List[str]]:
    """A file's definitions, all of them, and for each term the program
    whose top is the line the reference prints after it."""
    defs: Dict[str, str] = {}
    terms: List[str] = []
    for kind, item in read(text):
        if kind == "define":
            defs.update(item)
        else:
            terms.append(item)
    progs = [" ".join(f"{t} {POP}" for t in terms[:k]) + " " + terms[k] for k in range(len(terms))]
    return defs, progs


#: the reader's probe cap for a file, whose last program is all its terms
FILE_STEPS = 2_000_000_000


def run_file(text: str, form: str = "interpreted") -> List[str]:
    import skilark
    saved = skilark.STEPS
    skilark.STEPS = max(saved, FILE_STEPS)
    try:
        return _run_file(text, form)
    finally:
        skilark.STEPS = saved


def _run_file(text: str, form: str) -> List[str]:
    """The lines the reference prints running the file: the top after each
    term, ``run time error`` where a term errs, nothing where the stack is
    empty.  Interpreted by default, whose quotations read back as written."""
    from . import compiled, interpreted
    make = interpreted if form == "interpreted" else compiled
    own, progs = programs(text)
    defs = dict(joy.DEFINITIONS, **own)
    names = {f"t{i}": p for i, p in enumerate(progs)}
    run = make(names, defs)
    lines: List[str] = []
    for name in names:
        (kind, stack), _ = run.run("u" + name)
        if kind == "RErr":
            lines.append("run time error")
        elif kind == "RTime":
            lines.append("out of fuel")
        elif stack:
            top = stack[-1]
            lines.append(write(value(top)) if form == "interpreted" else write_compiled(top))
    return lines


def write_compiled(v: Any) -> str:
    """A compiled stack item: a quotation is read by its outcome, not its
    text, so it prints as ``[...]``."""
    if isinstance(v, tuple) and v and v[0] == "quot":
        return "[...]"
    return write(value(v))
