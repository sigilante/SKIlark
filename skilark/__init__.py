"""SKIlark: Joy on SKIjack.

The language is ``programs/joy.<lexicon>.ski`` (phase 1: the kernel and a
hand-written set of programs) and ``programs/kernel.ascii.ski`` (the same
kernel, alone, for the front end).  ``skilark.joy`` turns Joy text into
SKIjack source in three forms; this module compiles them with ``skijack``
and reads their data back behaviourally.

    >>> from skilark import Joy, interpreted, compiled
    >>> Joy().run("r1")                              # 1 2 + dup +
    (('RVal', [6]), 9276)
    >>> compiled({"p": "1 2 + dup +"}).run("up")     # no interpreter present
    (('RVal', [6]), 493)
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

import skijack
from aviary_kernel.terms import App, Atom
from skijack import ast as A
from skijack.probe import Prober
from skijack.run import decode, peel, run_level0, run_level1

from . import joy

__all__ = ["DIR", "Joy", "Run", "compiled", "interpreted", "level1", "read",
           "__version__"]
__version__ = "0.2.0"

#: the directory holding the ``.ski`` sources
DIR = pathlib.Path(__file__).parent / "programs"

#: the host contraction cap for a level-0 run and for every probe
STEPS = 5_000_000

Outcome = Tuple[str, Optional[List[Any]]]


def read(stem: str = "joy", lexicon: str = "ascii") -> str:
    """The source of a program in one lexicon."""
    return (DIR / f"{stem}.{lexicon}.ski").read_text(encoding="utf-8")


class Run:
    """A compiled SKIjack program in one of the front end's forms, with
    readers for its data.

    Stacks are returned bottom to top, as Joy writes them.  A quotation
    is read by its *form*: interpreted, as its list of words (a ``Lit``
    as ``("Lit", n)``); compiled, extensionally, as ``("quot", outcome)``
    where the outcome is the quotation applied to the empty stack, since
    a defunctionalized quotation has no list to read.
    """

    def __init__(self, source: str, mode: str, lexicon: str = "ascii"):
        self.source, self.mode, self.lexicon = source, mode, lexicon
        self.e = skijack.compile(source, lexicon=lexicon)
        self.pr = Prober(self.e)
        self.t = self.e.types

    # ------------------------------------------------------------ readers

    def prog(self, term) -> List[Any]:
        ctor, fields = peel(term, self.t["prog"], max_steps=STEPS)
        if ctor == "Done":
            return []
        w, wf = peel(fields[0], self.t["word"], max_steps=STEPS)
        word: Any = w
        if wf:
            word = (w, self.pr.read_nat(wf[0]) if w == "Lit" else self.prog(wf[0]))
        return [word] + self.prog(fields[1])

    def quot(self, term) -> Tuple[str, Outcome]:
        e = self.e
        return ("quot", self.result(App(App(e.terms["applyU"], term), e.terms["Empty"])))

    def stack(self, term) -> List[Any]:
        items: List[Any] = []
        while True:
            ctor, fields = peel(term, self.t["stack"], max_steps=STEPS)
            if ctor == "Empty":
                return items[::-1]
            kind, payload = peel(fields[0], self.t["item"], max_steps=STEPS)
            if kind == "Num":
                items.append(self.pr.read_nat(payload[0]))
            elif self.mode == "compiled":
                items.append(self.quot(payload[0]))
            else:
                items.append(self.prog(payload[0]))
            term = fields[1]

    def result(self, term) -> Outcome:
        ctor, fields = peel(term, self.t["result"], max_steps=STEPS)
        return (ctor, self.stack(fields[0]) if ctor == "RVal" else None)

    # ------------------------------------------------------------ running

    def run(self, name: str, max_steps: int = STEPS) -> Tuple[Outcome, int]:
        """A declared run's outcome and its host contraction count.  At
        level 1 the outcome is the interpreter's (``RValN`` carrying the
        encoded result, which is decoded and read; ``RTimeN``, ``RErrN``
        or ``RBlockN`` as themselves)."""
        if self.mode != "level1":
            term = self.e.terms[name]
            return self.result(term), run_level0(term, max_steps).steps
        p = self.e.level1[name]
        out = run_level1(p, max_steps)
        ctor, fields = peel(out.term, p.result_type, max_steps=STEPS)
        if ctor != "RValN":
            return (ctor, None), out.steps
        return _read_atoms(_term(decode(fields[0], p.object_type, max_steps=STEPS))), out.steps


#: the level-1 reader's spellings of the outcomes (joy.LEVEL1_READER)
_ATOM_OUTCOMES = {"K": "Yes", "K I": "No", "S S": "OEmpty", "S K K": "OQuot",
                  "S K": "RErr", "S I": "RTime"}


def _read_atoms(term) -> Outcome:
    """The answer is a combinator applied to atoms: the ABI's booleans
    ``K`` and ``K I``, or ``S`` applied to atoms for another outcome."""
    r = run_level0(term, STEPS)
    head, args = r.term, []
    while isinstance(head, App):
        args.append(head.arg)
        head = head.fn
    args.reverse()
    if isinstance(head, Atom) and all(isinstance(a, Atom) for a in args):
        key = " ".join([head.name] + [a.name for a in args])
        if key in _ATOM_OUTCOMES:
            return (_ATOM_OUTCOMES[key], None)
    raise ValueError(f"not a level-1 answer: {key if isinstance(head, Atom) else head!r}")


def _term(expr: A.Expr):
    """A decoded object-language expression (S, K, I and application)
    back as a host term, so the readers can probe it."""
    if isinstance(expr, A.Name):
        return Atom(expr.name)
    if isinstance(expr, A.App):
        return App(_term(expr.fn), _term(expr.arg))
    raise TypeError(f"not an object-language term: {expr!r}")


def interpreted(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS
                ) -> Run:
    """Each program as a ``prog`` datum under the kernel's ``exec``:
    ``rP`` fuelled (one unit per word), ``uP`` unfuelled."""
    return Run(joy.interpreted(programs, defs), "interpreted")


def compiled(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS
             ) -> Run:
    """Each program as the composition of its words, quotations
    defunctionalized: ``rP`` under ``apply fuel`` (one unit per
    quotation applied), ``uP`` under ``applyU``."""
    return Run(joy.compiled(programs, defs), "compiled")


def level1(programs: Dict[str, str], namespace: Sequence[str], fuel: int,
           defs: Dict[str, str] = joy.DEFINITIONS, form: str = "interpreted",
           value: int = 0) -> Run:
    """Each program run by ``wfN`` over the unfuelled kernel of ``form``,
    with the named definitions as namespace facts read by scry.  ``rP``
    asks whether the final top of stack is ``value`` and ``nP`` whether it
    is ``value + 1``; the outcome is ``("Yes", None)`` or ``("No", None)``,
    or another outcome by name."""
    return Run(joy.level1(programs, namespace, fuel, defs, form, value), "level1")


class Joy(Run):
    """The phase-1 artifact ``programs/joy.<lexicon>.ski``: the kernel and
    its hand-written programs, in either lexicon."""

    def __init__(self, lexicon: str = "ascii"):
        super().__init__(read("joy", lexicon), "interpreted", lexicon)

    def exec(self, prog_name: str, fuel: str = "fuel") -> Outcome:
        """``exec <fuel> <prog> Empty``, built here rather than declared."""
        e = self.e
        term = App(App(App(e.terms["exec"], e.terms[fuel]), e.terms[prog_name]),
                   e.terms["Empty"])
        return self.result(term)
