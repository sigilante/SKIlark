"""SKIlark predicates for lean-ski's zero-knowledge circuit.

lean-ski proves, in zero knowledge, a **predicate over literal bits**: a
public verifier ``V`` accepts a public ``x`` on ``n`` hidden bits, which the
circuit constrains to Scott Booleans (``K`` or ``K I``) and hands to ``V``
as ``boolsT``, each bit paired with the rest.  ``V`` is a SKIlark program:
it runs on the stack ``x`` above the decoded bits and accepts when it
leaves a nonzero numeral on top, returning ``K`` itself.  ``source``
returns the SKIjack text of ``V``, which lean-ski compiles itself;
``Terms`` builds ``x`` and the bits.

The first predicate, ``split``: ``vsplitB x r`` decodes ``2k`` bits into
the bits of two numbers ``a`` and ``b`` (interleaved, least significant
first) and accepts when ``a + b = x`` in ``k`` bits.  ``x`` is one
quotation ``X_0``, ``X_i = [X_{i+1} x_i]`` and ``X_{k-1} = [x_{k-1}]``.
Each step unpacks ``x_i`` with ``i``, sets the rest of ``X`` aside, and
branches on ``x_i``, the carry, ``a_i`` and ``b_i``: a bit other than
``0`` or ``1``, or a sum bit other than ``x_i``, fails (``0 i`` errs), and
the last step fails on a carry out.  ``tests/test_zk.py`` checks it on
every bit pattern at ``k`` = 2 and 3 (and it was run on all 4,096 at
``k = 4``), and on samples at ``k = 8``.

Two limits:

- ``vsplit``, the same program over a hidden *term* ``w`` rather than
  bits, can be fooled: a term answers the verifier's case analysis however
  it likes, and ``K (K (RVal R))``, with ``R`` a stack of ``2k - 1``
  zeros, is no stack at all and passes at ``x`` = 0 and 1 (pinned in the
  tests).  That is why lean-ski proves ``vsplitB`` over literal bits.
- the claim is weak: some ``a, b < 2^k`` add up to every ``x < 2^k``
  (``a = x``, ``b = 0``), so an accepted proof shows only ``x < 2^k``.  A
  range proof needs a commitment binding the hidden number to something
  public.
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


def decoder(n: int) -> str:
    """``decBits``: ``n`` literal bits, the last alone and each before it
    paired with the rest (lean-ski's ``boolsT``), to a stack of numerals,
    the first on top.  A Scott pair applies its argument to its two
    halves; a Scott Boolean selects: ``K`` is 1, ``K I`` is 0."""
    if n < 1:
        raise ValueError("n must be positive")
    body = f"Push (bitNum qr{n - 1}) Empty"
    for i in range(n - 2, -1, -1):
        body = f"qr{i} (\\qb{i}. \\qr{i + 1}. Push (bitNum qb{i}) ({body}))"
    return f"decBits qr0 = {body}\n"


#: the predicate's verifier: ``vsplit`` on the decoded bits
BITS = """
-- the verifier over literal bits (lean-ski's predicate statements)
bitNum b = b (Num (Suc Zero)) (Num Zero)
vsplitB x r = vsplit x (decBits r)
"""


def source(k: int) -> str:
    """The SKIjack text of ``vsplit`` and ``vsplitB`` for width ``k``."""
    return joy.compiled({"split": split_program(k)}) + WRAPPER + BITS + decoder(2 * k)


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

    def bits(self, a: int, b: int, da: Optional[List[int]] = None, db: Optional[List[int]] = None):
        """The literal bits of ``a`` and ``b``, interleaved, as lean-ski's
        ``boolsT``: Scott Booleans in Scott pairs."""
        da = da if da is not None else bits(a, self.k)
        db = db if db is not None else bits(b, self.k)
        bs = [d for i in range(self.k) for d in (da[i], db[i])]
        K, I, S = Atom("K"), Atom("I"), Atom("S")
        def boolT(d):
            return K if d else App(K, I)
        def pairT(p, q):
            return App(App(S, App(App(S, I), App(K, p))), App(K, q))
        out = boolT(bs[-1])
        for d in reversed(bs[:-1]):
            out = pairT(boolT(d), out)
        return out

    def verify_bits(self, x, r, max_steps: int = 50_000_000):
        """``V x r`` for the predicate over literal bits, reduced."""
        res = run_level0(App(App(self.t["vsplitB"], x), r), max_steps)
        return isinstance(res.term, Atom) and res.term.name == "K", res.steps

    def verify(self, x, w, max_steps: int = 50_000_000):
        """``V x w`` reduced: whether it is exactly ``K``, and the steps."""
        r = run_level0(App(App(self.t["vsplit"], x), w), max_steps)
        return isinstance(r.term, Atom) and r.term.name == "K", r.steps


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("usage: python -m skilark.zk K   (the SKIjack source of split for width K)")
    sys.stdout.write(source(int(sys.argv[1])))
