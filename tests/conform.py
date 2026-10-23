"""SKIlark's outcomes in the reference model's terms (``joyref``), so that
a run of either form can be checked against the reference's."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from skilark import joy

import joyref

#: the definitions SKIlark has and the reference does not: Kerby's words
#: and the two programs; the reference runs them as user definitions
OWN = {k: v for k, v in joy.DEFINITIONS.items()
       if k in ("nip", "tuck", "rot", "sip", "k", "y", "sumto", "fact")}


def reference(text: str) -> Tuple[str, Optional[list]]:
    """The reference's outcome of a program."""
    return joyref.Joy(OWN).run(text)


def codes(text: Any) -> Tuple:
    """A string as SKIlark reads it, as its codes."""
    return tuple(map(ord, text)) if isinstance(text, str) else tuple(text)


def element(w: Any) -> Tuple:
    """An interpreted quotation's element as a reference value."""
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
    if kind == "Glyph":
        return ("C", v)
    if kind == "Text":
        return ("T", codes(v))
    raise ValueError(f"no reference value for {w!r}")


def value(v: Any) -> Tuple:
    """An interpreted stack item as a reference value."""
    if isinstance(v, bool):
        return ("B", v)
    if isinstance(v, int):
        return ("N", v)
    if isinstance(v, tuple) and v[0] == "Sym":
        return ("S", v[1])
    if isinstance(v, tuple) and v[0] == "Char":
        return ("C", v[1])
    if isinstance(v, tuple) and v[0] == "Str":
        return ("T", codes(v[1]))
    if isinstance(v, list):
        return ("L", tuple(element(w) for w in v))
    raise ValueError(f"no reference value for {v!r}")


def interpreted_outcome(out) -> Tuple[str, Optional[list]]:
    """An interpreted run's outcome in the reference's terms."""
    kind, stack = out
    return (kind, None if stack is None else [value(v) for v in stack])


def extensional(v: Tuple) -> Tuple:
    """A reference value as the compiled form can read one: a list by the
    outcome of running it on the empty stack, as ``("Q", outcome)``."""
    if v[0] != "L":
        return v
    run = joyref.Joy(OWN)
    s: list = []
    try:
        run.exe(s, v[1])
    except joyref.JoyError:
        return ("Q", ("RErr", None))
    return ("Q", ("RVal", [extensional(u) for u in s]))


def compiled_expectation(ref) -> Tuple[str, Optional[list]]:
    """The reference's outcome as the compiled form can read one."""
    kind, stack = ref
    return (kind, None if stack is None else [extensional(v) for v in stack])


def tagged(v: Any) -> Tuple:
    """A compiled stack item, tagged as the reference's values are."""
    if isinstance(v, bool):
        return ("B", v)
    if isinstance(v, int):
        return ("N", v)
    if v[0] == "Sym":
        return ("S", v[1])
    if v[0] == "Char":
        return ("C", v[1])
    if v[0] == "Str":
        return ("T", codes(v[1]))
    if v[0] == "quot":
        return ("Q", compiled_outcome(v[1]))
    raise ValueError(f"no reference value for {v!r}")


def compiled_outcome(out) -> Tuple[str, Optional[list]]:
    """A compiled run's outcome, tagged."""
    kind, stack = out
    return (kind, None if stack is None else [tagged(v) for v in stack])
