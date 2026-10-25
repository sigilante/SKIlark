"""``python -m skilark "3 [dup +] i"``: run a Joy program in the
interpreted and the compiled form and print each outcome with its host
contraction count.  ``python -m skilark FILE.joy`` runs a Joy file as the
reference does, printing the top of the stack after each term
(``skilark.joyfile``).  ``--ski`` shows instead the program as the
closed S, K, I term it runs as, its size, and what it reduces to;
``--ski-out FILE`` writes that term, as Avon's SKIT (``.skit``) or as
skijack's shared form (``.dag``), for ``avon reduce``.  ``--define "sq == dup +"`` adds a definition.
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
    ap.add_argument("program", help='Joy text, e.g. "1 2 + dup +", or a .joy file')
    ap.add_argument("--define", action="append", default=[], metavar="DEF",
                    help='a definition, "name == body"; may repeat')
    ap.add_argument("--form", choices=["interpreted", "compiled", "both"],
                    default="both")
    ap.add_argument("--ski", action="store_true",
                    help="show the program as its closed S, K, I term, and what it reduces to")
    ap.add_argument("--ski-out", metavar="FILE",
                    help="write that term: FILE.skit (Avon's SKIT) or FILE.dag (shared)")
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
    if args.ski or args.ski_out:
        form = "compiled" if args.form == "compiled" else "interpreted"
        try:
            return _ski(args.program, defs, form, args.ski_out)
        except (SkijackError, ValueError) as ex:
            print(f"skilark: {ex}", file=sys.stderr)
            return 1
    if args.program.endswith(".joy") and os.path.isfile(args.program):
        from .joyfile import JoyFileError, run_file
        with open(args.program, encoding="utf-8") as f:
            text = f.read()
        try:
            for line in run_file(text, "compiled" if args.form == "compiled" else "interpreted"):
                print(line)
        except (JoyFileError, SkijackError, ValueError) as ex:
            print(f"skilark: {args.program}: {ex}", file=sys.stderr)
            return 1
        return 0
    forms = ["interpreted", "compiled"] if args.form == "both" else [args.form]
    try:
        return _run(forms, args.program, defs)
    except SkijackError as ex:                  # a reducer misconfigured, say
        print(f"skilark: {ex}", file=sys.stderr)
        return 1


#: the most atoms --ski prints a term in full
SKI_SHOWN = 2_000


def _ski(program, defs, form, out) -> int:
    """The program (or a .joy file's terms, the reference's last line) as
    the closed S, K, I term it runs as: its size, the term itself when it
    is small, and the outcome it reduces to."""
    from skijack.export import jam
    from skijack.probe import dag_size
    from aviary_kernel.terms import pretty
    from . import joyfile
    if program.endswith(".joy") and os.path.isfile(program):
        with open(program, encoding="utf-8") as f:
            own, progs = joyfile.programs(f.read())
        if not progs:
            raise ValueError(f"{program} has no term")
        defs, program = dict(defs, **own), progs[-1]
    run = (interpreted if form == "interpreted" else compiled)({"p": program}, defs)
    term = run.e.terms["up"]
    atoms = run.e.sizes["up"]
    print(f"{form}: {atoms:,} atoms as a tree, {dag_size(term):,} nodes shared")
    if atoms <= SKI_SHOWN:
        print(pretty(term))
    if out:
        if out.endswith(".dag"):
            from skijack.avon import _encode
            text, _ = _encode(term)
            with open(out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        else:
            with open(out, "wb") as f:
                f.write(jam(term))
        print(f"wrote {out}")
    (ctor, stack), steps = run.run("up")
    shown = ctor if stack is None else " ".join(_show(x) for x in stack)
    print(f"reduces in {steps:,} contractions to {shown}")
    return 0


def _run(forms, program, defs) -> int:
    for form in forms:
        run = (interpreted if form == "interpreted" else compiled)({"p": program}, defs)
        for pre, label in (("u", "unfuelled"), ("r", "fuelled")):
            (ctor, stack), steps = run.run(pre + "p")
            shown = ctor if stack is None else " ".join(_show(x) for x in stack)
            print(f"{form:12} {label:10} {steps:>9,}  {shown}")
    return 0


def _show(x) -> str:
    """A stack item as Joy writes it."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, list):                       # interpreted quotation
        return "[" + " ".join(_word(w) for w in x) + "]"
    if isinstance(x, tuple) and x[0] == "quot":   # compiled: extensional
        ctor, stack = x[1]
        return "[" + (ctor if stack is None else " ".join(_show(y) for y in stack)) + "]"
    if isinstance(x, tuple) and x[0] == "Sym":
        return x[1]
    if isinstance(x, tuple) and x[0] == "Char":
        return _char(x[1])
    if isinstance(x, tuple) and x[0] == "Str":
        return _string(x[1])
    if isinstance(x, tuple) and x[0] == "Set":
        return _set(x[1])
    return str(x)


def _word(w) -> str:
    """An interpreted quotation's element as Joy writes it."""
    if isinstance(w, str):
        return joy.NAMES.get(w, w)
    kind, v = w
    if kind == "Lit":
        return str(v)
    if kind == "Truth":
        return "true" if v else "false"
    if kind == "Quote":
        return "[" + " ".join(_word(u) for u in v) + "]"
    if kind == "Glyph":
        return _char(v)
    if kind == "Text":
        return _string(v)
    if kind == "Set":
        return _set(v)
    return str(v)                                 # a Def, by its name


def _set(members) -> str:
    return "{" + " ".join(map(str, members)) + "}"


def _char(c: int) -> str:
    return f"'{chr(c)}" if 32 < c < 127 else f"'\\{c:03d}"


def _string(s) -> str:
    codes = [ord(c) for c in s] if isinstance(s, str) else list(s)
    return '"' + "".join(chr(c) if 32 <= c < 127 and c not in (34, 92) else f"\\{c:03d}"
                         for c in codes) + '"'


if __name__ == "__main__":
    sys.exit(main())
