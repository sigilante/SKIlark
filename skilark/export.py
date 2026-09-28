"""Export SKIlark's workloads for Avon (PLAN.md §3, phase 3: the census).

    python3 -m skilark.export OUTDIR

Writes one SKIT container per run and ``OUTDIR/manifest.tsv`` in the format
of SKIjack's ``skijack.export`` (``avon/DESIGN.md`` §10.1): phase 1's
declared runs (``joy.phase1.r1`` ...), and phase 2's eight programs in the
interpreted and compiled forms, unfuelled and fuelled
(``joy.interpreted.up1``, ``joy.compiled.rp7`` ...).  Each line carries the
reference host's status and contraction count for weak head normal form
and the result constructor the run peels to; the payload is a stack, so
the object-type and payload columns are ``-``.

It also writes the workloads' dictionary, ``dictionary.tsv`` and
``dictionary_names.tsv``, in SKIjack's format, so a census can name the
subterms it finds.
"""

from __future__ import annotations

import pathlib
import sys

from aviary_kernel.terms import pretty
from skijack.dictionary import from_expansion
from skijack.export import jam
from skijack.run import peel, run_level0

from . import Joy, compiled, interpreted

__all__ = ["PROGRAMS", "runs", "export"]

STEPS = 5_000_000

#: phase 2's programs, as tests/test_modes.py pins them
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


def _ctors(decl) -> str:
    return " ".join(f"{c.name}/{len(c.fields)}" for c in decl.ctors)


def runs():
    """(form, compiled program, [run names]) for every workload."""
    phase1 = Joy()
    names1 = sorted((k for k in phase1.e.terms
                     if k[:1] == "r" and k[1:2].isdigit()),
                    key=lambda k: (len(k), k))
    interp = interpreted(PROGRAMS)
    comp = compiled(PROGRAMS)
    names2 = [f"{m}{p}" for p in sorted(PROGRAMS) for m in ("u", "r")]
    return [("phase1", phase1, names1), ("interpreted", interp, names2),
            ("compiled", comp, names2)]


def export(outdir: pathlib.Path) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    lines, rows, names = [], {}, []
    for form, run, which in runs():
        rdecl = run.t["result"]
        for name in which:
            term = run.e.terms[name]
            ident = f"joy.{form}.{name}"
            (outdir / f"{ident}.skit").write_bytes(jam(term))
            out = run_level0(term, STEPS)
            ctor = "-"
            if out.status.name == "WHNF":
                ctor, _ = peel(out.term, rdecl, max_steps=STEPS)
            lines.append("\t".join([ident, f"{ident}.skit", str(STEPS),
                                    out.status.name, str(out.steps),
                                    _ctors(rdecl), "-", ctor, "-"]))
        d = from_expansion(run.e)
        for n in d.names():
            e = d[n]
            rows.setdefault(e.hash, (e.size, pretty(e.term)))
            names.append((f"skilark-{form}", n, e.hash))
    (outdir / "manifest.tsv").write_text("\n".join(lines) + "\n")
    (outdir / "dictionary.tsv").write_text("".join(
        f"{h}\t{size}\t{text}\n" for h, (size, text) in sorted(rows.items())))
    (outdir / "dictionary_names.tsv").write_text("".join(
        f"{form}\t{n}\t{h}\n" for form, n, h in names))
    return len(lines)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python3 -m skilark.export OUTDIR", file=sys.stderr)
        return 2
    n = export(pathlib.Path(argv[0]))
    print(f"{n} runs written to {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.setrecursionlimit(1_000_000)
    sys.exit(main())
