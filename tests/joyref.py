"""A model of Joy's reference semantics, for checking SKIlark against.

The reference is Wodan58/Joy (github.com/Wodan58/Joy, fe9fa0f, 2026-03-31),
the maintained descendant of von Thun's joy1.  Each builtin below follows
its C source (``src/<name>.c`` and the macros of ``runtime.h``), cited by
file; the comments say where the reference's checks fall.  It covers the
types SKIlark has: integers, truth values, characters, strings, sets,
lists and symbols.  Floats, files and the other words are not modelled, and
neither are two artefacts of the reference's C strings: a string ends at
a character 0, and its characters above 127 read back negative where C's
``char`` is signed.

Values are tagged tuples:

    ("N", n)        an integer (the reference's are 64-bit; these are not)
    ("B", b)        a truth value
    ("C", n)        a character, its code
    ("T", (n, ..))  a string, its characters' codes
    ("Z", bits)     a set of 0 to 63, its 64 bits as a natural
    ("L", (x, ..))  a list: a quotation is a list of its elements
    ("S", name)     a symbol: a word inside a quotation

A run returns ``("RVal", stack)``, the stack bottom first, or
``("RErr", None)`` for any of the reference's ``execerror`` calls.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

Value = Tuple
Stack = List[Value]


class JoyError(Exception):
    """The reference's ``execerror``: the run stops with an error."""


class Undefined(Exception):
    """A run whose outcome the reference leaves to its C representation,
    which the model does not follow."""


#: scan.c ``special``: the escapes after a backslash
ESCAPES = {"b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "'": 39, "\\": 92}


def _special(text: str, i: int) -> Tuple[int, int]:
    """scan.c ``special``, at the character after a backslash: the code and
    the index past the escape.  Up to three decimal digits are a code."""
    c = text[i]
    if c in ESCAPES:
        return ESCAPES[c], i + 1
    if c.isdigit():
        j = i + 1
        while j < len(text) and j < i + 3 and text[j].isdigit():
            j += 1
        return int(text[i:j]), j
    return ord(c), i + 1


#: globals.h SETSIZE, and a set's bits
SETSIZE = 64
MASK = (1 << SETSIZE) - 1


def list2set(members: list) -> Value:
    """factor.c ``list2set``: a set literal's integers and characters,
    each 0 to 63; anything else is the reader's error."""
    bits = 0
    for t in members:
        code = t if isinstance(t, int) else t[1] if isinstance(t, tuple) and t[0] == "C" else None
        if code is None or not 0 <= code < SETSIZE:
            raise ValueError(f"not a set member: {t!r}")
        bits |= 1 << code
    return ("Z", bits)


def parse(text: str) -> list:
    """Joy text as tokens, as scan.c reads it: integers, names, nested
    lists, ``("C", n)`` for ``'c``, ``("T", codes)`` for ``"..."`` and
    ``("Z", bits)`` for ``{...}``."""
    out: list = [[]]
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c in "[{":
            out.append([]); i += 1
        elif c == "]":
            q = out.pop(); out[-1].append(q); i += 1
        elif c == "}":
            q = out.pop(); out[-1].append(list2set(q)); i += 1
        elif c == "'":
            if text[i + 1] == "\\":
                code, i = _special(text, i + 2)
            else:
                code, i = ord(text[i + 1]), i + 2
            out[-1].append(("C", code))
        elif c == '"':
            i += 1
            codes = []
            while text[i] != '"':
                if text[i] == "\\":
                    code, i = _special(text, i + 1)
                else:
                    code, i = ord(text[i]), i + 1
                codes.append(code)
            out[-1].append(("T", tuple(codes))); i += 1
        else:
            j = i
            while j < len(text) and not text[j].isspace() and text[j] not in "[]{}":
                j += 1
            t = text[i:j]; i = j
            out[-1].append(int(t) if t.lstrip("-").isdigit() and t != "-" else t)
    assert len(out) == 1, "unbalanced"
    return out[0]


def literal(t) -> Value:
    """A token as the value a quotation holds: the reader makes numerals
    integers, ``true`` and ``false`` truth values, brackets lists and every
    other name a symbol."""
    if isinstance(t, int):
        return ("N", t)
    if isinstance(t, tuple):
        return t
    if isinstance(t, list):
        return ("L", tuple(literal(u) for u in t))
    if t in ("true", "false"):
        return ("B", t == "true")
    return ("S", t)


# ------------------------------------------------------------------ helpers

def num(v: Value) -> int:
    """``nodevalue(...).num`` of a truth value, character or integer."""
    return int(v[1])


def numeric(v: Value) -> bool:
    """``NUMERICTYPE``: an integer, character or truth value."""
    return v[0] in ("N", "B", "C")


def is_null(v: Value) -> bool:
    """compare.h ``is_null``."""
    if numeric(v):
        return num(v) == 0
    if v[0] in ("L", "T", "Z"):
        return not v[1]
    return False                                    # USR_, ANON_FUNCT_


def signed(bits: int) -> int:
    """A set's bits as ``nodevalue(...).num`` reads them, an int64_t."""
    return bits - (1 << SETSIZE) if bits >> (SETSIZE - 1) else bits


def unsigned(v: Value) -> int:
    """comprel.h's ``nodevalue(...).num`` as a uint64_t, for SETCMP: a
    set's bits, a number's two's complement.  A list's, a string's or a
    symbol's is a C pointer, which the model does not follow."""
    if v[0] == "Z":
        return v[1]
    if numeric(v) and -(1 << 63) <= num(v) < (1 << 63):
        return num(v) & MASK
    raise Undefined("a set compared by < with a value that is not a number")


def name(v: Value):
    """A symbol's or a string's characters, as strcmp reads them."""
    return tuple(ord(c) for c in v[1]) if v[0] == "S" else v[1]


def compare(a: Value, b: Value) -> int:
    """compare.h ``Compare``: -1, 0 or 1, and 1 for values of kinds it does
    not order."""
    if is_null(a) and is_null(b):
        return 0
    if a[0] in ("S", "T"):
        if b[0] in ("S", "T"):                      # strcmp on the names
            x, y = name(a), name(b)
            return (x > y) - (x < y)
        return 1
    if numeric(a) or a[0] == "Z":                   # a set's bits as an int64_t
        if numeric(b) or b[0] == "Z":
            x = signed(a[1]) if a[0] == "Z" else num(a)
            y = signed(b[1]) if b[0] == "Z" else num(b)
            return (x > y) - (x < y)
        return 1
    return 1                                        # LIST_


def truth(v: Value) -> bool:
    """boolean.h ``get_boolean``."""
    if numeric(v):
        return num(v) != 0
    if v[0] in ("L", "T", "Z"):
        return bool(v[1])
    return True                                     # USR_, ANON_FUNCT_


def int64(n: int) -> int:
    """An integer result, which the reference keeps in an int64_t: past
    that range its C arithmetic overflows, which the model does not
    follow."""
    if not -(1 << 63) <= n < (1 << 63):
        raise Undefined("an integer past 64 bits")
    return n


def c_div(a: int, b: int) -> int:
    """C's ``/``: truncation toward zero."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def c_rem(a: int, b: int) -> int:
    """C's ``%``: the remainder takes the dividend's sign."""
    return a - b * c_div(a, b)


# ------------------------------------------------------------- the machine

class Joy:
    """The reference's interpreter over the modelled types.  ``defs`` are
    user definitions (``name == body``), run by name and quoted as
    symbols, as the reference's ``USR_`` words are."""

    def __init__(self, defs: Optional[Dict[str, str]] = None, steps: int = 200_000):
        self.defs = {k: parse(v) for k, v in (defs or {}).items()}
        self.steps = steps
        self.b: Dict[str, Callable[[Stack], None]] = {}
        for name in dir(self):
            if name.startswith("w_"):
                self.b[BUILTIN_NAMES.get(name[2:], name[2:])] = getattr(self, name)

    # -- running

    def run(self, text: str) -> Tuple[str, Optional[List[Value]]]:
        s: Stack = []
        try:
            self.exe(s, [literal(t) if not isinstance(t, str) or t in ("true", "false")
                         else ("S", t) for t in parse(text)])
        except JoyError:
            return ("RErr", None)
        return ("RVal", s)

    def exe(self, s: Stack, prog) -> None:
        """``exeterm``: push each literal, run each symbol."""
        for v in prog:
            self.steps -= 1
            if self.steps < 0:
                raise RuntimeError("the model ran out of steps")
            if v[0] == "S":
                self.word(s, v[1])
            else:
                s.append(v)

    def word(self, s: Stack, name: str) -> None:
        if name in self.b:
            self.b[name](s)
        elif name in self.defs:
            self.exe(s, [literal(t) for t in self.defs[name]])
        else:
            raise KeyError(f"no definition of {name!r}")

    def quote(self, v: Value) -> tuple:
        return v[1]

    # -- the checks of runtime.h

    @staticmethod
    def params(s: Stack, n: int) -> None:
        if len(s) < n:
            raise JoyError("parameters")

    @staticmethod
    def quotes(s: Stack, n: int) -> None:
        """ONEQUOTE .. FOURQUOTES: the top n are lists."""
        for k in range(1, n + 1):
            if s[-k][0] != "L":
                raise JoyError("quotation")

    # -- stack words

    def w_dup(self, s):                 # dup.c
        self.params(s, 1); s.append(s[-1])

    def w_swap(self, s):                # swap.c
        self.params(s, 2); s[-1], s[-2] = s[-2], s[-1]

    def w_pop(self, s):                 # pop.c
        self.params(s, 1); s.pop()

    def w_over(self, s):                # over.c
        self.params(s, 2); s.append(s[-2])

    def w_dupd(self, s):                # dupd.c: [dup] dip
        self.params(s, 2); z = s.pop(); s.append(s[-1]); s.append(z)

    def w_swapd(self, s):               # swapd.c: [swap] dip
        self.params(s, 3); z = s.pop(); s[-1], s[-2] = s[-2], s[-1]; s.append(z)

    def w_popd(self, s):                # popd.c: [pop] dip
        self.params(s, 2); z = s.pop(); s.pop(); s.append(z)

    def w_rollup(self, s):              # rollup.c: X Y Z -> Z X Y
        self.params(s, 3); x, y, z = s[-3:]; s[-3:] = [z, x, y]

    def w_rolldown(self, s):            # rolldown.c: X Y Z -> Y Z X
        self.params(s, 3); x, y, z = s[-3:]; s[-3:] = [y, z, x]

    def w_rotate(self, s):              # rotate.c: X Y Z -> Z Y X
        self.params(s, 3); x, y, z = s[-3:]; s[-3:] = [z, y, x]

    def w_id(self, s):                  # id.c
        pass

    def w_stack(self, s):               # stack.c: the stack as a list, top first
        s.append(("L", tuple(reversed(s))))

    def w_unstack(self, s):             # unstack.c
        self.params(s, 1)
        if s[-1][0] != "L":
            raise JoyError("list")
        lst = s.pop()[1]
        s[:] = list(reversed(lst))

    # -- aggregates: lists, strings and sets

    @staticmethod
    def aggregate(v: Value) -> None:
        if v[0] not in ("L", "T", "Z"):
            raise JoyError("aggregate")

    @staticmethod
    def members(v: Value) -> list:
        """An aggregate's members: a string's are characters, a set's its
        integers, ascending."""
        if v[0] == "Z":
            return [("N", i) for i in range(SETSIZE) if v[1] >> i & 1]
        return [("C", c) for c in v[1]] if v[0] == "T" else list(v[1])

    @staticmethod
    def build(kind: str, members: list) -> Value:
        """An aggregate of ``kind`` from its members."""
        if kind == "T":
            return ("T", tuple(m[1] for m in members))
        if kind == "Z":
            bits = 0
            for m in members:
                bits |= 1 << num(m)
            return ("Z", bits)
        return ("L", tuple(members))

    @staticmethod
    def member(x: Value) -> int:
        """runtime.h CHECKSETMEMBER: an integer or a character, 0 to 63."""
        if x[0] not in ("N", "C") or not 0 <= x[1] < SETSIZE:
            raise JoyError("small numeric")
        return x[1]

    def consed(self, a: Value, x: Value) -> Value:
        """cons_swons.h: a list takes any member, a string a character, a
        set a small number."""
        self.aggregate(a)
        if a[0] == "T" and x[0] != "C":
            raise JoyError("character")
        if a[0] == "Z":
            return ("Z", a[1] | 1 << self.member(x))
        return self.build(a[0], [x] + self.members(a))

    def w_cons(self, s):                # cons.c: X A -> B
        self.params(s, 2)
        a = s.pop(); x = s.pop(); s.append(self.consed(a, x))

    def w_swons(self, s):               # swons.c: A X -> B
        self.params(s, 2)
        x = s.pop(); a = s.pop(); s.append(self.consed(a, x))

    def nonempty(self, v: Value) -> list:
        self.aggregate(v)
        if not v[1]:
            raise JoyError("non-empty aggregate")
        return self.members(v)

    def w_first(self, s):               # first.c
        self.params(s, 1)
        s.append(self.nonempty(s.pop())[0])

    def w_rest(self, s):                # rest.c
        self.params(s, 1)
        a = s.pop(); s.append(self.build(a[0], self.nonempty(a)[1:]))

    def w_uncons(self, s):              # uncons.c: A -> F R
        self.params(s, 1)
        a = s.pop(); m = self.nonempty(a)
        s.append(m[0]); s.append(self.build(a[0], m[1:]))

    def w_unswons(self, s):             # unswons.c: A -> R F
        self.w_uncons(s); self.w_swap(s)

    def w_concat(self, s):              # concat.c: SAME2TYPES, then the aggregate
        self.params(s, 2)
        if s[-1][0] != s[-2][0]:
            raise JoyError("same types")
        self.aggregate(s[-1])
        b = s.pop(); a = s.pop()
        s.append(("Z", a[1] | b[1]) if a[0] == "Z" else (a[0], a[1] + b[1]))

    def w_size(self, s):                # size.c
        self.params(s, 1)
        self.aggregate(s[-1])
        s.append(("N", len(self.members(s.pop()))))

    def w_null(self, s):                # null.c: symbols are not null
        self.params(s, 1); s.append(("B", is_null(s.pop())))

    def w_small(self, s):               # small.c
        self.params(s, 1)
        v = s.pop()
        if numeric(v):
            s.append(("B", num(v) < 2))
        elif v[0] in ("L", "T", "Z"):
            s.append(("B", len(self.members(v)) < 2))
        else:
            raise JoyError("different type")

    @staticmethod
    def index(v: Value) -> int:
        """runtime.h POSITIVEINDEX: an integer or truth value, not negative."""
        if v[0] not in ("N", "B") or num(v) < 0:
            raise JoyError("non-negative integer")
        return num(v)

    def w_take(self, s):                # take.c: A N -> B
        self.params(s, 2)
        n = self.index(s.pop())
        self.aggregate(s[-1])
        a = s.pop(); s.append(self.build(a[0], self.members(a)[:n]))

    def w_drop(self, s):                # drop.c: A N -> B
        self.params(s, 2)
        n = self.index(s.pop())
        self.aggregate(s[-1])
        a = s.pop(); s.append(self.build(a[0], self.members(a)[n:]))

    def w_at(self, s):                  # at.c, of_at.h: A I -> X
        self.params(s, 2)
        i = self.index(s[-1])
        self.aggregate(s[-2])
        a = self.members(s[-2])
        if i >= len(a):
            raise JoyError("smaller index")
        s.pop(); s.pop(); s.append(a[i])

    def w_of(self, s):                  # of.c, of_at.h: I A -> X
        self.w_swap(s); self.w_at(s)

    # -- arithmetic (plusminus.h, mul.c, divide.c, rem.c)

    def plusminus(self, s, op):
        self.params(s, 2)
        if s[-1][0] != "N":
            raise JoyError("integer")
        if s[-2][0] not in ("N", "C"):              # NUMERIC2: integer or char
            raise JoyError("numeric second parameter")
        b = s.pop(); a = s.pop(); s.append((a[0], int64(op(a[1], b[1]))))

    def w_plus(self, s):
        self.plusminus(s, lambda a, b: a + b)

    def w_minus(self, s):
        self.plusminus(s, lambda a, b: a - b)

    def w_mul(self, s):
        self.params(s, 2)
        if s[-1][0] != "N" or s[-2][0] != "N":
            raise JoyError("two integers")
        b = s.pop(); a = s.pop(); s.append(("N", int64(a[1] * b[1])))

    def w_divide(self, s):
        self.params(s, 2)
        if s[-1][0] == "N" and s[-1][1] == 0:       # CHECKDIVISOR first
            raise JoyError("non-zero divisor")
        if s[-1][0] != "N" or s[-2][0] != "N":
            raise JoyError("two integers")
        b = s.pop(); a = s.pop(); s.append(("N", int64(c_div(a[1], b[1]))))

    def w_rem(self, s):
        self.params(s, 2)
        if s[-1][0] != "N" or s[-2][0] != "N":
            raise JoyError("two integers")
        if s[-1][1] == 0:                           # CHECKZERO
            raise JoyError("non-zero operand")
        b = s.pop(); a = s.pop(); s.append(("N", c_rem(a[1], b[1])))

    def predsucc(self, s, d):           # predsucc.h: truth values give integers
        self.params(s, 1)
        if not numeric(s[-1]):
            raise JoyError("numeric")
        v = s.pop(); s.append(("C" if v[0] == "C" else "N", int64(num(v) + d)))

    def w_succ(self, s):
        self.predsucc(s, 1)

    def w_pred(self, s):
        self.predsucc(s, -1)

    def maxmin(self, s, take_second):   # maxmin.h: SAME2TYPES, NUMERICTYPE
        self.params(s, 2)
        if s[-1][0] != s[-2][0]:
            raise JoyError("same types")
        if not numeric(s[-1]):
            raise JoyError("numeric")
        kind = "C" if s[-1][0] == "C" else "N"
        y = num(s.pop()); x = num(s.pop())
        s.append((kind, x if take_second(y, x) else y))

    def w_max(self, s):                 # max: top < second ? second : top
        self.maxmin(s, lambda y, x: y < x)

    def w_min(self, s):                 # min: top > second ? second : top
        self.maxmin(s, lambda y, x: y > x)

    def integer1(self, s) -> int:
        """runtime.h FLOAT then the integer case: abs, sign, neg."""
        self.params(s, 1)
        if s[-1][0] != "N":
            raise JoyError("float or integer")
        return s.pop()[1]

    def w_abs(self, s):
        s.append(("N", int64(abs(self.integer1(s)))))

    def w_sign(self, s):
        n = self.integer1(s); s.append(("N", (n > 0) - (n < 0)))

    def w_neg(self, s):
        s.append(("N", int64(-self.integer1(s))))

    def w_ord(self, s):                 # ord.c, ordchr.h
        self.params(s, 1)
        if not numeric(s[-1]):
            raise JoyError("numeric")
        s.append(("N", num(s.pop())))

    def w_chr(self, s):                 # chr.c, ordchr.h
        self.params(s, 1)
        if not numeric(s[-1]):
            raise JoyError("numeric")
        s.append(("C", num(s.pop())))

    def has(self, a: Value, x: Value) -> bool:
        """inhas.h: a list by the comparison, a string by character code, a
        set by a small number's bit."""
        self.aggregate(a)
        if a[0] == "Z":
            return bool(a[1] >> self.member(x) & 1)
        if a[0] == "T":
            return numeric(x) and num(x) in a[1]
        return any(compare(m, x) == 0 for m in a[1])

    def w_has(self, s):                 # has.c: A X -> B
        self.params(s, 2)
        x = s.pop(); a = s.pop(); s.append(("B", self.has(a, x)))

    def w_in(self, s):                  # in.c: X A -> B
        self.params(s, 2)
        a = s.pop(); x = s.pop(); s.append(("B", self.has(a, x)))

    # -- comparison (comprel.h, comprel2.h): = and != compare, the orders
    #    take a set's bits (SETCMP) when either value is a set

    def comprel(self, s, test, setcmp=None):
        self.params(s, 2)
        if setcmp and "Z" in (s[-1][0], s[-2][0]):
            j = unsigned(s[-1]); i = unsigned(s[-2])
            s.pop(); s.pop(); s.append(("B", setcmp(i, j)))
            return
        y = s.pop(); x = s.pop(); s.append(("B", test(compare(x, y))))

    def w_eql(self, s):
        self.comprel(s, lambda c: c == 0)

    def w_neql(self, s):
        self.comprel(s, lambda c: c != 0)

    def w_less(self, s):
        self.comprel(s, lambda c: c < 0, lambda i, j: i != j and not i & ~j)

    def w_leql(self, s):
        self.comprel(s, lambda c: c <= 0, lambda i, j: not i & ~j)

    def w_greater(self, s):
        self.comprel(s, lambda c: c > 0, lambda i, j: i != j and not j & ~i)

    def w_geql(self, s):
        self.comprel(s, lambda c: c >= 0, lambda i, j: not j & ~i)

    # -- truth values (not.c, andorxor.h)

    def w_not(self, s):                 # not.c: a set's complement
        self.params(s, 1)
        if s[-1][0] == "Z":
            s.append(("Z", ~s.pop()[1] & MASK))
            return
        if not numeric(s[-1]):
            raise JoyError("different type")
        s.append(("B", num(s.pop()) == 0))

    def andorxor(self, s, op, setop):
        self.params(s, 2)
        if s[-1][0] != s[-2][0]:
            raise JoyError("same types")
        if s[-1][0] == "Z":
            y = s.pop()[1]; x = s.pop()[1]; s.append(("Z", setop(x, y)))
            return
        if not numeric(s[-1]):
            raise JoyError("different type")
        y = num(s.pop()); x = num(s.pop()); s.append(("B", op(x, y)))

    def w_and(self, s):
        self.andorxor(s, lambda x, y: bool(x and y), lambda x, y: x & y)

    def w_or(self, s):
        self.andorxor(s, lambda x, y: bool(x or y), lambda x, y: x | y)

    def w_xor(self, s):
        self.andorxor(s, lambda x, y: x != y, lambda x, y: x ^ y)

    # -- combinators

    def w_i(self, s):                   # i.c
        self.params(s, 1); self.quotes(s, 1); self.exe(s, s.pop()[1])

    def w_x(self, s):                   # x.c: [P] x == [P] P
        self.params(s, 1); self.quotes(s, 1); self.exe(s, s[-1][1])

    def w_dip(self, s):                 # dip.c
        self.params(s, 2); self.quotes(s, 1)
        p = s.pop(); x = s.pop(); self.exe(s, p[1]); s.append(x)

    def w_branch(self, s):              # branch.c: B [T] [F]
        self.params(s, 3); self.quotes(s, 2)
        f = s.pop(); t = s.pop(); b = s.pop()
        self.exe(s, t[1] if truth(b) else f[1])

    def test(self, s: Stack, p) -> bool:
        """Run P on a copy of the stack and read its top as a truth value
        (CHECKSTACK: an empty stack is an error)."""
        c = list(s)
        self.exe(c, p)
        if not c:
            raise JoyError("non-empty stack")
        return truth(c[-1])

    def w_ifte(self, s):                # ifte.c
        self.params(s, 3); self.quotes(s, 3)
        f = s.pop(); t = s.pop(); b = s.pop()
        self.exe(s, t[1] if self.test(s, b[1]) else f[1])

    def w_nullary(self, s):             # nullary.c, n_ary.h
        self.params(s, 1); self.quotes(s, 1)
        p = s.pop(); c = list(s); self.exe(c, p[1])
        if not c:
            raise JoyError("value to push")
        s.append(c[-1])

    def w_infra(self, s):               # infra.c: L1 [P] -> L2
        self.params(s, 2); self.quotes(s, 1)
        if s[-2][0] != "L":
            raise JoyError("list as second parameter")
        p = s.pop(); l1 = s.pop()
        c = list(reversed(l1[1])); self.exe(c, p[1])
        s.append(("L", tuple(reversed(c))))

    def w_times(self, s):               # times.c: N [P]
        self.params(s, 2); self.quotes(s, 1)
        if s[-2][0] != "N":
            raise JoyError("integer as second parameter")
        p = s.pop(); n = s.pop()[1]
        for _ in range(n):
            self.exe(s, p[1])

    def w_while(self, s):               # while.c: [B] [D]
        self.params(s, 2); self.quotes(s, 2)
        d = s.pop(); b = s.pop()
        while self.test(s, b[1]):
            self.exe(s, d[1])

    def w_tailrec(self, s):             # tailrec.c: [P] [T] [R1]
        self.params(s, 3); self.quotes(s, 3)
        r1 = s.pop(); t = s.pop(); p = s.pop()
        while not self.test(s, p[1]):
            self.exe(s, r1[1])
        self.exe(s, t[1])

    def w_linrec(self, s):              # linrec.c: [P] [T] [R1] [R2]
        self.params(s, 4); self.quotes(s, 4)
        r2 = s.pop(); r1 = s.pop(); t = s.pop(); p = s.pop()

        def aux():
            if self.test(s, p[1]):
                self.exe(s, t[1])
            else:
                self.exe(s, r1[1]); aux(); self.exe(s, r2[1])
        aux()

    def w_binrec(self, s):              # binrec.c: [P] [T] [R1] [R2]
        self.params(s, 4); self.quotes(s, 4)
        r2 = s.pop(); r1 = s.pop(); t = s.pop(); p = s.pop()

        def aux():
            if self.test(s, p[1]):
                self.exe(s, t[1])
            else:
                self.exe(s, r1[1])
                self.params(s, 1)
                second = s.pop(); aux(); s.append(second); aux()
                self.exe(s, r2[1])
        aux()

    def w_genrec(self, s):              # genrec.c, genrecaux.c
        self.params(s, 4); self.quotes(s, 4)
        for _ in range(3):
            self.w_cons(s)
        self.genrecaux(s)

    def genrecaux(self, s):
        g = s.pop()[1]                              # [[B] [T] [R1] R2..]
        if self.test(s, g[0][1]):
            self.exe(s, g[1][1])
        else:
            self.exe(s, g[2][1])
            s.append(("L", (("L", g), ("S", "#genrecaux"))))
            self.exe(s, g[3:])

    def w_genrecaux(self, s):           # the anonymous word genrec pushes
        self.genrecaux(s)

    def w_primrec(self, s):             # primrec.c: X [I] [C]
        self.params(s, 3); self.quotes(s, 2)
        c = s.pop(); i = s.pop(); x = s.pop()
        if x[0] in ("L", "T", "Z"):
            members = self.members(x)
        elif x[0] == "N":
            members = [("N", k) for k in range(x[1], 0, -1)]
        else:
            raise JoyError("different type")
        s.extend(members)
        self.exe(s, i[1])
        for _ in members:
            self.exe(s, c[1])

    def w_map(self, s):                 # map.c: A [P] -> B
        self.params(s, 2); self.quotes(s, 1)
        self.aggregate(s[-2])
        p = s.pop(); a = s.pop(); out = []
        for v in self.members(a):
            c = s + [v]; self.exe(c, p[1])
            if not c:
                raise JoyError("non-empty stack")
            out.append(c[-1])
        if a[0] == "T":                             # str[j++] = num, a C char
            if not all(numeric(v) for v in out):
                raise Undefined("map on a string to a non-number")
            out = [("C", (num(v) + 128) % 256 - 128) for v in out]
        if a[0] == "Z":                             # set |= 1 << num, unchecked
            if not all(numeric(v) and 0 <= num(v) < SETSIZE for v in out):
                raise Undefined("map on a set to a value that is not a member")
        s.append(self.build(a[0], out))

    def w_filter(self, s):              # filter.c: A [B] -> A1
        self.params(s, 2); self.quotes(s, 1)
        self.aggregate(s[-2])
        p = s.pop(); a = s.pop()
        s.append(self.build(a[0], [v for v in self.members(a) if self.test(s + [v], p[1])]))

    def w_step(self, s):                # step.c: A [P]
        self.params(s, 2); self.quotes(s, 1)
        p = s.pop(); a = s.pop()
        self.aggregate(a)
        for v in self.members(a):
            s.append(v); self.exe(s, p[1])

    def w_fold(self, s):                # fold.c: swapd step
        self.params(s, 3); self.w_swapd(s); self.w_step(s)

    # -- types (typeof.c, type.h, sametype.c; globals.h numbers them)

    def kind(self, v: Value) -> int:
        """``nodetype``: a symbol is a builtin (ANON_FUNCT_, 3) or a user
        definition (USR_, 2), as the reader made it."""
        if v[0] == "S":
            return 3 if v[1] in self.b else 2
        return {"B": 4, "C": 5, "N": 6, "Z": 7, "T": 8, "L": 9}[v[0]]

    def w_typeof(self, s):
        self.params(s, 1); s.append(("N", self.kind(s.pop())))

    def type_test(self, s, test):       # type.h TYPE: ONEPARAM, then the test
        self.params(s, 1); s.append(("B", test(self.kind(s.pop()))))

    def w_integer(self, s):
        self.type_test(s, lambda k: k == 6)

    def w_char(self, s):
        self.type_test(s, lambda k: k == 5)

    def w_logical(self, s):
        self.type_test(s, lambda k: k == 4)

    def w_set(self, s):
        self.type_test(s, lambda k: k == 7)

    def w_string(self, s):
        self.type_test(s, lambda k: k == 8)

    def w_list(self, s):
        self.type_test(s, lambda k: k == 9)

    def w_leaf(self, s):
        self.type_test(s, lambda k: k != 9)

    def w_user(self, s):
        self.type_test(s, lambda k: k == 2)

    def w_float(self, s):               # no value here is a float or a file
        self.type_test(s, lambda k: k == 10)

    def w_file(self, s):
        self.type_test(s, lambda k: k == 11)

    def w_sametype(self, s):            # a builtin on top: the same builtin
        self.params(s, 2)
        y = s.pop(); x = s.pop()
        if self.kind(y) == 3:
            same = self.kind(x) == 3 and x[1] == y[1]
        else:
            same = self.kind(x) == self.kind(y)
        s.append(("B", same))

    # -- SKIlark's own kernel words, from Kerby's basis: not Joy's, so the
    #    reference has them as definitions; these are what they define

    def w_unit(self, s):                # [X]
        self.params(s, 1); s.append(("L", (s.pop(),)))

    def w_cat(self, s):                 # [A] [B] -> [A B], quotations only
        self.params(s, 2); self.quotes(s, 2)
        b = s.pop(); a = s.pop(); s.append(("L", a[1] + b[1]))


#: the builtins whose names are not Python identifiers
BUILTIN_NAMES = {
    "plus": "+", "minus": "-", "mul": "*", "divide": "/", "eql": "=",
    "neql": "!=", "less": "<", "leql": "<=", "greater": ">", "geql": ">=",
    "genrecaux": "#genrecaux",
}
