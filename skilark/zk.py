"""SKIlark statements for lean-ski's zero-knowledge circuit.

The circuit proves, in zero knowledge, that a hidden term ``w`` makes a
public verifier ``V x w`` evaluate to ``K``.  A SKIlark statement is a
Joy predicate: ``V x w`` runs the program on the stack ``x`` above ``w``
(``appendS x w``) and accepts when it returns a nonzero numeral on top.
``source`` returns the SKIjack text of ``V`` (``vsplit``), which the
verifier compiles itself; ``Terms`` builds ``x`` and ``w``.

The first statement, ``split``, is that some hidden term ``w`` makes
``vsplit x w`` reduce to ``K``.  On a witness that is a stack of bit
numerals it reads two numbers ``a`` and ``b`` below ``2^k`` and accepts
exactly when ``a + b = x``.  Numbers are bits, least significant first.
The hidden ``w`` is a stack of ``2k`` numerals, ``a_0 b_0 a_1 b_1 …``;
the public ``x`` is one quotation ``X_0``, ``X_i = [X_{i+1} x_i]`` and
``X_{k-1} = [x_{k-1}]``.  Each step unpacks ``x_i`` with ``i``, sets the
rest of ``X`` aside, and branches on ``x_i``, the carry, ``a_i`` and
``b_i``: a bit other than ``0`` or ``1``, or a sum bit other than
``x_i``, fails (``0 i`` errs), and the last step fails on a carry out.

What an accepted ``w`` shows is weaker, in two ways, and this module is
the path from a SKIlark program to a proof, not a range proof:

- ``w`` is a term, and a term answers the verifier's case analysis however
  it likes: ``K (K (RVal R))``, with ``R`` a stack of ``2k - 1`` zeros, is
  no stack at all and passes at ``x`` = 0 and 1 (``tests/test_zk.py`` pins
  it at ``k`` = 2 and 8).  A claim about data needs the witness as
  literal bits the circuit constrains to Booleans.
- some ``a, b < 2^k`` add up to every ``x < 2^k`` (``a = x``, ``b = 0``),
  so even a well-formed witness shows only that ``x < 2^k``.  A range
  proof needs a commitment binding the hidden number to something public.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from aviary_kernel.terms import App, Atom
from skijack.run import run_level0

from . import Run, joy

#: the wrapper: ``V x w`` is ``accept`` of the program on ``x`` above ``w``
WRAPPER = """
-- the verifier: the program on the stack x above w, accepted when it
-- returns a nonzero numeral on top (skilark.zk)
bool === T | F
appendS s t = s |> { Empty t; Push a u (Push a (appendS u t)) }
accept r = r |> { RVal s (s |> { Empty F; Push a t (a |> { Num n (n |> { Zero F; Suc m T }); Quot q F }) }); RErr F; RTime F }
vsplit x w = accept (csplit applyU (appendS x w))
"""


def _case(z: str, o: str) -> str:
    """Branch on the bit on top: 0 runs ``z``, 1 runs ``o``, anything else
    fails."""
    return f"[{z}] [[{o}] [0 i] ifz] ifz"


def _leaf(x: int, c: int, a: int, b: int, last: bool) -> str:
    t = a + b + c
    if t % 2 != x:
        return "0 i"
    if last:
        return "1" if t < 2 else "0 i"
    return str(t // 2)


def _tree(last: bool) -> str:
    """Stack ``x c a b`` to the new carry (or, last, to ``1``)."""
    return _case(*[_case(*[_case(*[_case(_leaf(x, c, a, 0, last), _leaf(x, c, a, 1, last))
                                   for a in (0, 1)]) for c in (0, 1)]) for x in (0, 1)])


def _step(last: bool) -> str:
    """Stack ``X c a b …`` to ``X' c' …``; the last step leaves ``1``."""
    if last:
        return "i " + _tree(True)
    return "i swap [" + _tree(False) + "] dip"


def split_program(k: int) -> str:
    """The Joy predicate: carry ``0`` under ``X``, then ``k`` unrolled steps."""
    if k < 1:
        raise ValueError("k must be positive")
    return "0 swap " + " ".join([_step(False)] * (k - 1) + [_step(True)])


def source(k: int) -> str:
    """The SKIjack text of ``vsplit`` for width ``k``."""
    return joy.compiled({"split": split_program(k)}) + WRAPPER


# ------------------------------------------------------------ encoders

def bits(n: int, k: int) -> List[int]:
    """``n``'s ``k`` bits, least significant first."""
    return [n >> i & 1 for i in range(k)]


class Terms:
    """Terms of a compiled ``source``: the constructors, ``vsplit``, and
    the encoders of ``x`` and ``w``."""

    def __init__(self, k: int):
        self.k = k
        self.run = Run(source(k), "compiled")
        self.t = self.run.e.terms

    def app(self, f: str, *args):
        out = self.t[f]
        for a in args:
            out = App(out, a)
        return out

    def num(self, n: int):
        v = self.t["Zero"]
        for _ in range(n):
            v = App(self.t["Suc"], v)
        return App(self.t["Num"], v)

    def quot(self, items: Iterable):
        """A data quotation pushing ``items`` in order."""
        items = list(items)
        q = self.app("QUnit", items[-1])
        for it in reversed(items[:-1]):
            q = self.app("QCons", it, q)
        return App(self.t["Quot"], q)

    def stack(self, items: Iterable):
        """A Scott stack, first item on top."""
        s = self.t["Empty"]
        for it in reversed(list(items)):
            s = self.app("Push", it, s)
        return s

    def x(self, x: int, digits: Optional[List[int]] = None):
        ds = digits if digits is not None else bits(x, self.k)
        q = self.quot([self.num(ds[-1])])
        for d in reversed(ds[:-1]):
            q = self.quot([q, self.num(d)])
        return self.stack([q])

    def w(self, a: int, b: int, da: Optional[List[int]] = None, db: Optional[List[int]] = None):
        da = da if da is not None else bits(a, self.k)
        db = db if db is not None else bits(b, self.k)
        return self.stack([self.num(d) for i in range(self.k) for d in (da[i], db[i])])

    def verify(self, x, w, max_steps: int = 50_000_000):
        """``V x w`` reduced: whether it is exactly ``K``, and the steps."""
        r = run_level0(App(App(self.t["vsplit"], x), w), max_steps)
        return isinstance(r.term, Atom) and r.term.name == "K", r.steps


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("usage: python -m skilark.zk K   (the SKIjack source of split for width K)")
    sys.stdout.write(source(int(sys.argv[1])))
