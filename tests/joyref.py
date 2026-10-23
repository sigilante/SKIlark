"""A model of Joy's reference semantics, for checking SKIlark against.

The reference is Wodan58/Joy (github.com/Wodan58/Joy, fe9fa0f, 2026-03-31),
the maintained descendant of von Thun's joy1.  Each builtin below follows
its C source (``src/<name>.c`` and the macros of ``runtime.h``), cited by
file; the comments say where the reference's checks fall.  It covers the
types SKIlark has: integers, truth values, lists and symbols.  Floats,
files, sets and the other words are not modelled.

Values are tagged tuples:

    ("N", n)        an integer (the reference's are 64-bit; these are not)
    ("B", b)        a truth value
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


def parse(text: str) -> list:
    """Joy text as tokens: integers, names and nested lists."""
    toks = text.replace("[", " [ ").replace("]", " ] ").split()
    out: list = [[]]
    for t in toks:
        if t == "[":
            out.append([])
        elif t == "]":
            q = out.pop()
            out[-1].append(q)
        elif t.lstrip("-").isdigit() and t != "-":
            out[-1].append(int(t))
        else:
            out[-1].append(t)
    assert len(out) == 1, "unbalanced"
    return out[0]


def literal(t) -> Value:
    """A token as the value a quotation holds: the reader makes numerals
    integers, ``true`` and ``false`` truth values, brackets lists and every
    other name a symbol."""
    if isinstance(t, int):
        return ("N", t)
    if isinstance(t, list):
        return ("L", tuple(literal(u) for u in t))
    if t in ("true", "false"):
        return ("B", t == "true")
    return ("S", t)


# ------------------------------------------------------------------ helpers

def num(v: Value) -> int:
    """``nodevalue(...).num`` of a truth value or integer."""
    return int(v[1])


def numeric(v: Value) -> bool:
    """``NUMERICTYPE``: an integer, character or truth value."""
    return v[0] in ("N", "B")


def is_null(v: Value) -> bool:
    """compare.h ``is_null``."""
    if v[0] in ("N", "B"):
        return num(v) == 0
    if v[0] == "L":
        return not v[1]
    return False                                    # USR_, ANON_FUNCT_


def compare(a: Value, b: Value) -> int:
    """compare.h ``Compare``: -1, 0 or 1, and 1 for values of kinds it does
    not order."""
    if is_null(a) and is_null(b):
        return 0
    if a[0] == "S":
        if b[0] == "S":
            return (a[1] > b[1]) - (a[1] < b[1])
        return 1
    if a[0] in ("N", "B"):
        if b[0] in ("N", "B"):
            return (num(a) > num(b)) - (num(a) < num(b))
        return 1
    return 1                                        # LIST_


def truth(v: Value) -> bool:
    """boolean.h ``get_boolean``."""
    if v[0] in ("N", "B"):
        return num(v) != 0
    if v[0] == "L":
        return bool(v[1])
    return True                                     # USR_, ANON_FUNCT_


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

    # -- quotations and lists

    def w_cons(self, s):                # cons.c: X A -> B
        self.params(s, 2)
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        a = s.pop(); x = s.pop(); s.append(("L", (x,) + a[1]))

    def w_swons(self, s):               # swons.c: A X -> B
        self.params(s, 2)
        if s[-2][0] != "L":
            raise JoyError("aggregate")
        x = s.pop(); a = s.pop(); s.append(("L", (x,) + a[1]))

    def w_first(self, s):               # first.c
        self.params(s, 1)
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        if not s[-1][1]:
            raise JoyError("non-empty list")
        s.append(s.pop()[1][0])

    def w_rest(self, s):                # rest.c
        self.params(s, 1)
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        if not s[-1][1]:
            raise JoyError("non-empty list")
        s.append(("L", s.pop()[1][1:]))

    def w_uncons(self, s):              # uncons.c: A -> F R
        self.params(s, 1)
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        if not s[-1][1]:
            raise JoyError("non-empty list")
        a = s.pop()[1]; s.append(a[0]); s.append(("L", a[1:]))

    def w_unswons(self, s):             # unswons.c: A -> R F
        self.w_uncons(s); self.w_swap(s)

    def w_concat(self, s):              # concat.c: SAME2TYPES, then the aggregate
        self.params(s, 2)
        if s[-1][0] != s[-2][0]:
            raise JoyError("same types")
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        b = s.pop(); a = s.pop(); s.append(("L", a[1] + b[1]))

    def w_size(self, s):                # size.c
        self.params(s, 1)
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        s.append(("N", len(s.pop()[1])))

    def w_null(self, s):                # null.c: symbols are not null
        self.params(s, 1); s.append(("B", is_null(s.pop())))

    def w_small(self, s):               # small.c
        self.params(s, 1)
        v = s.pop()
        if v[0] in ("N", "B"):
            s.append(("B", num(v) < 2))
        elif v[0] == "L":
            s.append(("B", len(v[1]) < 2))
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
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        s.append(("L", s.pop()[1][:n]))

    def w_drop(self, s):                # drop.c: A N -> B
        self.params(s, 2)
        n = self.index(s.pop())
        if s[-1][0] != "L":
            raise JoyError("aggregate")
        s.append(("L", s.pop()[1][n:]))

    def w_at(self, s):                  # at.c, of_at.h: A I -> X
        self.params(s, 2)
        i = self.index(s[-1])
        if s[-2][0] != "L":
            raise JoyError("aggregate")
        a = s[-2][1]
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
        if s[-2][0] != "N":                         # NUMERIC2: integer or char
            raise JoyError("numeric second parameter")
        b = s.pop(); a = s.pop(); s.append(("N", op(a[1], b[1])))

    def w_plus(self, s):
        self.plusminus(s, lambda a, b: a + b)

    def w_minus(self, s):
        self.plusminus(s, lambda a, b: a - b)

    def w_mul(self, s):
        self.params(s, 2)
        if s[-1][0] != "N" or s[-2][0] != "N":
            raise JoyError("two integers")
        b = s.pop(); a = s.pop(); s.append(("N", a[1] * b[1]))

    def w_divide(self, s):
        self.params(s, 2)
        if s[-1][0] == "N" and s[-1][1] == 0:       # CHECKDIVISOR first
            raise JoyError("non-zero divisor")
        if s[-1][0] != "N" or s[-2][0] != "N":
            raise JoyError("two integers")
        b = s.pop(); a = s.pop(); s.append(("N", c_div(a[1], b[1])))

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
        s.append(("N", num(s.pop()) + d))

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
        y = num(s.pop()); x = num(s.pop())
        s.append(("N", x if take_second(y, x) else y))

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
        s.append(("N", abs(self.integer1(s))))

    def w_sign(self, s):
        n = self.integer1(s); s.append(("N", (n > 0) - (n < 0)))

    def w_neg(self, s):
        s.append(("N", -self.integer1(s)))

    # -- comparison (comprel.h, comprel2.h; no sets here)

    def comprel(self, s, test):
        self.params(s, 2)
        y = s.pop(); x = s.pop(); s.append(("B", test(compare(x, y))))

    def w_eql(self, s):
        self.comprel(s, lambda c: c == 0)

    def w_neql(self, s):
        self.comprel(s, lambda c: c != 0)

    def w_less(self, s):
        self.comprel(s, lambda c: c < 0)

    def w_leql(self, s):
        self.comprel(s, lambda c: c <= 0)

    def w_greater(self, s):
        self.comprel(s, lambda c: c > 0)

    def w_geql(self, s):
        self.comprel(s, lambda c: c >= 0)

    # -- truth values (not.c, andorxor.h)

    def w_not(self, s):
        self.params(s, 1)
        if not numeric(s[-1]):
            raise JoyError("different type")
        s.append(("B", num(s.pop()) == 0))

    def andorxor(self, s, op):
        self.params(s, 2)
        if s[-1][0] != s[-2][0]:
            raise JoyError("same types")
        if not numeric(s[-1]):
            raise JoyError("different type")
        y = num(s.pop()); x = num(s.pop()); s.append(("B", op(x, y)))

    def w_and(self, s):
        self.andorxor(s, lambda x, y: bool(x and y))

    def w_or(self, s):
        self.andorxor(s, lambda x, y: bool(x or y))

    def w_xor(self, s):
        self.andorxor(s, lambda x, y: x != y)

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
        if x[0] == "L":
            members = list(x[1])
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
        if s[-2][0] != "L":
            raise JoyError("aggregate")
        p = s.pop(); a = s.pop(); out = []
        for v in a[1]:
            c = s + [v]; self.exe(c, p[1])
            if not c:
                raise JoyError("non-empty stack")
            out.append(c[-1])
        s.append(("L", tuple(out)))

    def w_filter(self, s):              # filter.c: A [B] -> A1
        self.params(s, 2); self.quotes(s, 1)
        if s[-2][0] != "L":
            raise JoyError("aggregate")
        p = s.pop(); a = s.pop()
        out = tuple(v for v in a[1] if self.test(s + [v], p[1]))
        s.append(("L", out))

    def w_step(self, s):                # step.c: A [P]
        self.params(s, 2); self.quotes(s, 1)
        p = s.pop(); a = s.pop()
        if a[0] != "L":
            raise JoyError("aggregate")
        for v in a[1]:
            s.append(v); self.exe(s, p[1])

    def w_fold(self, s):                # fold.c: swapd step
        self.params(s, 3); self.w_swapd(s); self.w_step(s)

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
