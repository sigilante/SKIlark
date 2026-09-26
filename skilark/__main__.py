"""``python -m skilark "3 [dup +] i"``: run a Joy program in the
interpreted and the compiled form and print each outcome with its host
contraction count.  ``--define "sq == dup +"`` adds a definition."""

from __future__ import annotations

import argparse
import sys

from . import compiled, interpreted, joy


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="skilark",
                                 description="run a Joy program on SKIjack")
    ap.add_argument("program", help='Joy text, e.g. "1 2 + dup +"')
    ap.add_argument("--define", action="append", default=[], metavar="DEF",
                    help='a definition, "name == body"; may repeat')
    ap.add_argument("--form", choices=["interpreted", "compiled", "both"],
                    default="both")
    args = ap.parse_args(argv)
    defs = dict(joy.DEFINITIONS, **joy.parse_definitions("\n".join(args.define)))
    forms = ["interpreted", "compiled"] if args.form == "both" else [args.form]
    for form in forms:
        run = (interpreted if form == "interpreted" else compiled)({"p": args.program}, defs)
        for pre, label in (("u", "unfuelled"), ("r", "fuelled")):
            (ctor, stack), steps = run.run(pre + "p")
            shown = ctor if stack is None else " ".join(_show(x) for x in stack)
            print(f"{form:12} {label:10} {steps:>9,}  {shown}")
    return 0


def _show(x) -> str:
    if isinstance(x, list):                       # interpreted quotation
        return "[" + " ".join(str(w[1]) if isinstance(w, tuple) and w[0] == "Lit"
                              else str(w) for w in x) + "]"
    if isinstance(x, tuple) and x[0] == "quot":   # compiled: extensional
        ctor, stack = x[1]
        return "[" + (ctor if stack is None else " ".join(_show(y) for y in stack)) + "]"
    return str(x)


if __name__ == "__main__":
    sys.exit(main())
