"""SKIlark: Joy on SKIjack.

The language is the program ``programs/joy.<lexicon>.ski``; this module
only compiles it with ``skijack`` and reads its data back behaviourally.

    >>> from skilark import Joy
    >>> Joy().run("r1")          # 1 2 + dup +
    (('RVal', [6]), 9276)
"""

from __future__ import annotations

import pathlib
from typing import Any, List, Optional, Tuple

import skijack
from aviary_kernel.terms import App
from skijack.probe import Prober
from skijack.run import peel, run_level0

__all__ = ["DIR", "Joy", "read", "__version__"]
__version__ = "0.1.0"

#: the directory holding the ``.ski`` sources
DIR = pathlib.Path(__file__).parent / "programs"

#: the host contraction cap for every probe
STEPS = 5_000_000

Outcome = Tuple[str, Optional[List[Any]]]


def read(stem: str = "joy", lexicon: str = "ascii") -> str:
    """The source of a program in one lexicon."""
    return (DIR / f"{stem}.{lexicon}.ski").read_text(encoding="utf-8")


class Joy:
    """The compiled kernel, with readers for its data.

    Stacks are returned bottom to top, as Joy writes them; a quotation is
    returned as a list of words, a ``Lit`` as ``("Lit", n)``.
    """

    def __init__(self, lexicon: str = "ascii"):
        self.lexicon = lexicon
        self.e = skijack.compile(read("joy", lexicon), lexicon=lexicon)
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

    def stack(self, term) -> List[Any]:
        items: List[Any] = []
        while True:
            ctor, fields = peel(term, self.t["stack"], max_steps=STEPS)
            if ctor == "Empty":
                return items[::-1]
            kind, payload = peel(fields[0], self.t["item"], max_steps=STEPS)
            items.append(self.pr.read_nat(payload[0]) if kind == "Num"
                         else self.prog(payload[0]))
            term = fields[1]

    def result(self, term) -> Outcome:
        ctor, fields = peel(term, self.t["result"], max_steps=STEPS)
        return (ctor, self.stack(fields[0]) if ctor == "RVal" else None)

    # ------------------------------------------------------------ running

    def run(self, name: str) -> Tuple[Outcome, int]:
        """A declared run's outcome and its contraction count."""
        term = self.e.terms[name]
        return self.result(term), run_level0(term, STEPS).steps

    def exec(self, prog_name: str, fuel: str = "fuel") -> Outcome:
        """``exec <fuel> <prog> Empty``, built here rather than declared."""
        e = self.e
        term = App(App(App(e.terms["exec"], e.terms[fuel]), e.terms[prog_name]),
                   e.terms["Empty"])
        return self.result(term)
