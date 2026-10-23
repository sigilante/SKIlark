"""Phase 3's measurements: the kernel's loop and its fuel, in variants.

The kernel (``programs/kernel.ascii.ski``) runs a program by a fold that
*splices*: ``Do``, ``Dip`` and ``Ifz`` copy their quotation onto the
front of the continuation with ``cat``.  Its fuel is a Scott numeral,
``fuel := mul ten (add ten ten)``, decremented once per word.  This module
builds the same kernel with either piece replaced and runs the phase-2
programs through each, so the costs compare on the same programs and the
same reducer.

Loops, each with the kernel's words and errors:

``splice``
    the kernel's own: ``Do`` runs ``cat r q``.
``stack``
    the continuation as data, ``ctl === Halt | Ret prog ctl``: ``Do``
    runs ``r`` with ``Ret q k`` and copies nothing.
``sequenced``
    a quotation runs to its result, then the rest of the program runs on
    that result's stack; fuel, when there is fuel, comes back in the
    result.

Fuel, one unit per word in every form:

``computed``
    the kernel's own, ``mul ten (add ten ten)``.
``literal``
    the same numeral written out, ``Suc (Suc ... Zero)``.
``church``
    no numeral: the loop's body applied 200 times, ``c200 loopC timeC``,
    so a word costs one unfolding and nothing is decremented.  Only the
    splice loop takes it: the sequenced loop returns the fuel left in its
    result, and Church fuel left is a function, where the kernel keeps
    every field first-order.

``python -m skilark.variants`` prints the tables ``PLAN.md`` §3 records;
``tests/test_variants.py`` pins them.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from . import Run, joy
from .joy import DEFINITIONS, _programs, datum, nat

#: the phase-2 programs (``tests/test_modes.py``)
PROGRAMS = {
    "p1": "1 2 + dup +",
    "p2": "3 [dup +] i",
    "p3": "1 2 over",
    "p4": "1 [2] [3] k",
    "p5": "1 2 unit cons",
    "p6": "+",
    "p7": "3 sumto",
    "p8": "5 sumto",
}

FUEL = 200

_K = joy._kernel()
_STEP = _K[_K.index("step ex w q s = "):_K.index("-- The same loop without fuel")]


def _step(head: str, rest: str, do: str, dip: str, zero: str, suc: str) -> str:
    """The kernel's ``step`` under a new head, with its continuation sites
    rewritten: ``rest`` replaces ``ex q`` (the next word), and the four
    splices become ``do``, ``dip`` and ``ifz``'s ``zero`` and ``suc``."""
    s = _STEP.replace("step ex w q s = ", head + " = ", 1)
    for old, new in (("(ex q ", f"({rest} "),
                     ("(ex (cat r q) t)", do),
                     ("(ex (cat r (Then (wordOf b) q)) u)", dip),
                     ("(ex (cat z q) v)", zero),
                     ("(ex (cat sc q) (Push (Num m) v))", suc)):
        if old not in s:
            raise ValueError(f"the kernel's step has no {old!r}")
        s = s.replace(old, new)
    return s


def church(n: int) -> str:
    """``c<n> f x = f (f ... (f x))``, a Church numeral by its definition."""
    return f"c{n} f x = {'f (' * n}x{')' * n}\n"


STACK = """
-- the continuation as data: the programs still to run, innermost first
ctl === Halt | Ret prog ctl
execK f p k s = f |> { Zero RTime; Suc g (p |> { Done (k |> { Halt (RVal s); Ret q j (execK f q j s) }); Then w q (stepK (execK g) w q k s) }) }
execKU p k s = p |> { Done (k |> { Halt (RVal s); Ret q j (execKU q j s) }); Then w q (stepK execKU w q k s) }
""" + _step("stepK ex w q k s", "ex q k",
            "(ex r (Ret q k) t)", "(ex r (Ret (Then (wordOf b) q) k) u)",
            "(ex z (Ret q k) v)", "(ex sc (Ret q k) (Push (Num m) v))")

_SEQUENCED_F = _step("stepF ex g w q s", "ex g q",
                     "(seqF ex (ex g r t) q)", "(dipF ex (ex g r u) b q)",
                     "(seqF ex (ex g z v) q)", "(seqF ex (ex g sc (Push (Num m) v)) q)")

SEQUENCED = """
-- results sequenced: a quotation runs to its result, then the rest runs
-- on that result's stack; fuelled, the result carries the fuel left
fres === FVal stack nat | FErr | FTime
seqU ex r q = r |> { RVal u (ex q u); RErr RErr; RTime RTime }
dipU ex r b q = r |> { RVal v (ex q (Push b v)); RErr RErr; RTime RTime }
execN p s = p |> { Done (RVal s); Then w q (stepN execN w q s) }
seqF ex r q = r |> { FVal u h (ex h q u); FErr FErr; FTime FTime }
dipF ex r b q = r |> { FVal v h (ex h q (Push b v)); FErr FErr; FTime FTime }
execF f p s = f |> { Zero FTime; Suc g (p |> { Done (FVal s g); Then w q (stepF execF g w q s) }) }
toR r = r |> { FVal s h (RVal s); FErr RErr; FTime RTime }
""" + _step("stepN ex w q s", "ex q",
            "(seqU ex (ex r t) q)", "(dipU ex (ex r u) b q)",
            "(seqU ex (ex z v) q)", "(seqU ex (ex sc (Push (Num m) v)) q)") \
    + _SEQUENCED_F.replace("RErr", "FErr")

LITERAL = f"fuelL := {nat(FUEL)}\n"

CHURCH = """
-- fuel as a Church numeral: the loop's body, applied 200 times
loopC k p s = p |> { Done (RVal s); Then w q (step k w q s) }
timeC p s = RTime
""" + church(10) + """c20 f x = c10 f (c10 f x)
c200 f x = c10 (c20 f) x
execC := c200 loopC timeC
"""

#: (loop, fuel) -> (source added to the kernel, the fuelled run, the unfuelled run)
INTERPRETED: Dict[Tuple[str, str], Tuple[str, str, Optional[str]]] = {
    ("splice", "computed"):    ("", "exec fuel {p} Empty", "execU {p} Empty"),
    ("splice", "literal"):     (LITERAL, "exec fuelL {p} Empty", None),
    ("splice", "church"):      (CHURCH, "execC {p} Empty", None),
    ("stack", "computed"):     (STACK, "execK fuel {p} Halt Empty", "execKU {p} Halt Empty"),
    ("stack", "literal"):      (STACK + LITERAL, "execK fuelL {p} Halt Empty", None),
    ("sequenced", "computed"): (SEQUENCED, "toR (execF fuel {p} Empty)", "execN {p} Empty"),
    ("sequenced", "literal"):  (SEQUENCED + LITERAL, "toR (execF fuelL {p} Empty)", None),
}


def interpreted(loop: str, fuel: str, programs: Dict[str, str] = PROGRAMS) -> Run:
    """The kernel with ``loop`` and ``fuel``; for each program ``p``,
    ``pP`` its datum, ``rP`` the fuelled run and, where the loop has one,
    ``uP`` the unfuelled run."""
    extra, fuelled, unfuelled = INTERPRETED[(loop, fuel)]
    out = [_K, extra, "\n-- programs, from skilark.variants\n"]
    for name, prog in _programs(programs, DEFINITIONS).items():
        out.append(f"p{name} := {datum(prog)}\n")
        out.append(f"r{name} := {fuelled.format(p='p' + name)}\n")
        if unfuelled:
            out.append(f"u{name} := {unfuelled.format(p='p' + name)}\n")
    return Run("".join(out), "interpreted")


def compiled(fuel: str, programs: Dict[str, str] = PROGRAMS) -> Run:
    """The compiled form with ``fuel`` in its eliminator: ``rP`` fuelled,
    ``uP`` unfuelled, as ``skilark.compiled`` declares them."""
    src = joy.compiled(programs)
    if fuel == "computed":
        return Run(src, "compiled")
    if fuel == "literal":
        old = "fuel  := mul ten (add ten ten)"
        if old not in src:
            raise ValueError(f"the compiled kernel has no {old!r}")
        return Run(src.replace(old, f"fuel  := {nat(FUEL)}"), "compiled")
    if fuel != "church":
        raise ValueError(f"unknown fuel {fuel!r}")
    # applyC k: apply's cases with the next fuel level k for (apply g)
    a = src.index("apply f q s = ")
    line = src[a:src.index("\n", a)]
    cases = line[line.index("(q |> {") + len("(q |> {"):line.rindex("})")]
    cases = cases.replace("(apply g)", "k").replace("apply g ", "k ")
    src += ("\n-- fuel as a Church numeral: apply's cases, applied 200 times\n"
            f"applyC k q s = q |> {{{cases}}}\n"
            "timeQ q s = RTime\n" + church(10) +
            "c20 f x = c10 f (c10 f x)\nc200 f x = c10 (c20 f) x\n"
            "applyFC := c200 applyC timeQ\n")
    for name in programs:
        src = src.replace(f"r{name} := c{name} (apply fuel) Empty",
                          f"r{name} := c{name} applyFC Empty")
    return Run(src, "compiled")


def table(run: Run, programs: Dict[str, str] = PROGRAMS
          ) -> Dict[str, Tuple[Tuple[str, Optional[List]], int, Optional[int]]]:
    """For each program: its fuelled outcome, the fuelled host contraction
    count, and the unfuelled count where the variant has an unfuelled run
    (whose outcome must be the same)."""
    out = {}
    for p in programs:
        o, n = run.run("r" + p)
        u = None
        if "u" + p in run.e.terms:
            ou, u = run.run("u" + p)
            if ou != o:
                raise AssertionError(f"{p}: unfuelled {ou} but fuelled {o}")
        out[p] = (o, n, u)
    return out


def main() -> None:
    print("interpreted: host contractions, fuelled (unfuelled)")
    for (loop, fuel) in INTERPRETED:
        t = table(interpreted(loop, fuel))
        cells = " ".join(f"{n:>8,}" + (f" ({u:,})" if u is not None else "")
                         for _, n, u in t.values())
        print(f"  {loop:9} {fuel:8} {cells}", flush=True)
    print("compiled: host contractions, fuelled (unfuelled)")
    for fuel in ("computed", "literal", "church"):
        t = table(compiled(fuel))
        cells = " ".join(f"{n:>8,}" + (f" ({u:,})" if u is not None else "")
                         for _, n, u in t.values())
        print(f"  {fuel:8} {cells}", flush=True)


if __name__ == "__main__":
    main()
