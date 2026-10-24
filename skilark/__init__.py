"""SKIlark: Joy on SKIjack.

The language is ``programs/joy.<lexicon>.ski`` (phase 1: the kernel and a
hand-written set of programs) and ``programs/kernel.ascii.ski`` (the same
kernel, alone, for the front end).  ``skilark.joy`` turns Joy text into
SKIjack source in three forms; this module compiles them with ``skijack``
and reads their data back behaviourally.

    >>> from skilark import Joy, interpreted, compiled
    >>> Joy().run("r1")                              # 1 2 + dup +
    (('RVal', [6]), 2003)
    >>> compiled({"p": "1 2 + dup +"}).run("up")     # no interpreter present
    (('RVal', [6]), 493)
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

from aviary_kernel.terms import App, Atom
from skijack import ast as A
from skijack.probe import Prober
from skijack.run import decode, peel, run_level0, run_level1

from . import abstraction, joy

__all__ = ["DIR", "Joy", "Run", "compiled", "interpreted", "level1", "read",
           "__version__"]
__version__ = "0.9.0"

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
    is read by its *form*: interpreted, as its list of words (a literal by
    its kind, an integer ``("Lit", n)``); compiled, extensionally, as ``("quot", outcome)``
    where the outcome is the quotation applied to the empty stack, since
    a defunctionalized quotation has no list to read.
    """

    def __init__(self, source: str, mode: str, lexicon: str = "ascii"):
        self.source, self.mode, self.lexicon = source, mode, lexicon
        self.e = abstraction.compile(source, lexicon=lexicon)
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
            if w == "Def":
                word = (w, self.name(wf[0]))
            elif w == "Lit" and "named" in self.t:  # the kernel's: Lit of an item
                word = self.literal(wf[0])
            elif w == "Lit":                        # phase 1's and the basis's
                word = (w, self.number(wf[0]))
            else:
                word = (w, self.prog(wf[0]))
        return [word] + self.prog(fields[1])

    #: a literal's reading by its item's kind: an integer is ``("Lit", n)``
    _LITERALS = {"Num": "Lit", "Logical": "Truth", "Quot": "Quote", "Char": "Glyph",
                 "Str": "Text", "Set": "Set"}

    def literal(self, term) -> Tuple[str, Any]:
        """The kernel's ``Lit`` word, by its item: ``("Lit", n)``,
        ``("Truth", b)``, ``("Quote", words)``, ``("Glyph", n)``,
        ``("Text", s)`` or ``("Set", members)``."""
        kind, payload = peel(term, self.t["item"], max_steps=STEPS)
        if kind == "Num" or kind == "Char":
            v: Any = self.number(payload[0])
        elif kind == "Logical":
            v = peel(payload[0], self.t["logical"], max_steps=STEPS)[0] == "True"
        elif kind == "Str":
            v = self.string(payload[0])
        elif kind == "Quot":
            v = self.prog(payload[0])
        elif kind == "Set":
            v = self.members(payload[0])
        else:
            raise ValueError(f"no literal of kind {kind}")
        return (self._LITERALS[kind], v)

    def symbol(self, term) -> str:
        """A symbol by its Joy name: interpreted, its word's (a ``Def``'s
        own); compiled, its constructor's (``YDup`` is ``dup``, ``Zsize``
        is ``size``)."""
        if self.mode == "compiled":
            return joy.symbol_name(peel(term, self.t["sym"], max_steps=STEPS)[0])
        ctor, fields = peel(term, self.t["word"], max_steps=STEPS)
        return self.name(fields[0]) if ctor == "Def" else joy.NAMES[ctor]

    def name(self, term) -> str:
        """A ``Def``'s name, from its ``named`` field."""
        _, fields = peel(term, self.t["named"], max_steps=STEPS)
        return self.text(fields[0])

    def string(self, term):
        """A string's ``text``: its characters as a Python string, or as
        their codes when one has no character."""
        codes = []
        ctor, fields = peel(term, self.t["text"], max_steps=STEPS)
        while ctor == "TCons":
            codes.append(self.number(fields[0]))
            ctor, fields = peel(fields[1], self.t["text"], max_steps=STEPS)
        if all(0 <= c < 0x110000 for c in codes):
            return "".join(map(chr, codes))
        return tuple(codes)

    def members(self, term) -> Tuple[int, ...]:
        """A set's members, ascending."""
        out = []
        ctor, fields = peel(term, self.t["set"], max_steps=STEPS)
        while ctor == "SCons":
            out.append(self.pr.read_nat(fields[0]))
            ctor, fields = peel(fields[1], self.t["set"], max_steps=STEPS)
        return tuple(out)

    def text(self, term) -> str:
        """A name's ``text`` as a string: a letter is its place in the
        alphabet, an operator sign 62 less its code, negated."""
        out = []
        ctor, fields = peel(term, self.t["text"], max_steps=STEPS)
        while ctor == "TCons":
            c = self.number(fields[0])
            out.append(chr(96 + c if c > 0 else 63 + c))
            ctor, fields = peel(fields[1], self.t["text"], max_steps=STEPS)
        return "".join(out)

    def number(self, term) -> int:
        """A numeral: a natural, or where the program's numbers are integers
        (``Pos m`` is m, ``Neg m`` is -(m+1)), an integer."""
        if "int" not in self.t:
            return self.pr.read_nat(term)
        sign, fields = peel(term, self.t["int"], max_steps=STEPS)
        m = self.pr.read_nat(fields[0])
        return m if sign == "Pos" else -(m + 1)

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
                items.append(self.number(payload[0]))
            elif kind == "Logical":
                b, _ = peel(payload[0], self.t["logical"], max_steps=STEPS)
                items.append(b == "True")
            elif kind == "Sym":
                items.append(("Sym", self.symbol(payload[0])))
            elif kind == "Char":
                items.append(("Char", self.number(payload[0])))
            elif kind == "Str":
                items.append(("Str", self.string(payload[0])))
            elif kind == "Set":
                items.append(("Set", self.members(payload[0])))
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
                  "S S K": "OLogical", "S S I": "OSym", "S K S": "OChar", "S S S": "OStr",
                  "S I K": "OSet",
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
        """``exec <fuel> <prog> Empty``, built here rather than declared;
        ``fuel`` names a Church numeral (``fuel`` is 200, ``ten`` 10)."""
        e = self.e
        term = App(App(App(e.terms["exec"], e.terms[fuel]), e.terms[prog_name]),
                   e.terms["Empty"])
        return self.result(term)
