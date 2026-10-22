"""``python -m skilark "3 [dup +] i"``: run a Joy program in the
interpreted and the compiled form and print each outcome with its host
contraction count.  ``--define "sq == dup +"`` adds a definition.
``--reducer avon`` runs the reductions in Avon, the C runtime, and
``--reducer check`` in both, compared; either needs ``AVON``, the path of
an ``avon`` binary (skijack's ``SKIJACK_REDUCER``)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys

from skijack import SkijackError

from . import compiled, interpreted, joy


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="skilark",
                                 description="run a Joy program on SKIjack")
    ap.add_argument("program", help='Joy text, e.g. "1 2 + dup +"')
    ap.add_argument("--define", action="append", default=[], metavar="DEF",
                    help='a definition, "name == body"; may repeat')
    ap.add_argument("--form", choices=["interpreted", "compiled", "both"],
                    default="both")
    ap.add_argument("--reducer", choices=["aviary", "avon", "check"],
                    help="what reduces the terms: aviary in Python (the default), "
                         "Avon, or both compared; avon and check need AVON")
    args = ap.parse_args(argv)
    if args.reducer:
        if importlib.util.find_spec("skijack.avon") is None:
            ap.error("--reducer needs skijack 0.2.1 or later, which has skijack.avon, "
                     "the Avon reducer")
        os.environ["SKIJACK_REDUCER"] = args.reducer
    defs = dict(joy.DEFINITIONS, **joy.parse_definitions("\n".join(args.define)))
    forms = ["interpreted", "compiled"] if args.form == "both" else [args.form]
    try:
        return _run(forms, args.program, defs)
    except SkijackError as ex:                  # a reducer misconfigured, say
        print(f"skilark: {ex}", file=sys.stderr)
        return 1


def _run(forms, program, defs) -> int:
    for form in forms:
        run = (interpreted if form == "interpreted" else compiled)({"p": program}, defs)
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
