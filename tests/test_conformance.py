"""Joy's behaviour is the standard: every pinned outcome, in both forms, is
the reference implementation's (Wodan58/Joy, modelled in ``joyref``), but
for the deviations below, each pinned with its reason.

The pinned tables are checked against SKIjack runs in their own modules;
this module checks them against the reference, so it runs no reduction
but the deviations' own.
"""

import pytest

import conform
import joyref
import test_combinators as C
import test_modes as M
import test_text as T
import test_types as Y
import test_sets as Z
import test_library as B
import test_pure as P
import test_symbols as N
import test_numtext as X
import test_words as W
from skilark import compiled, interpreted

#: every program whose outcome some module pins: (module, name, text)
PINNED = ([("words", n, p) for n, p in W.PROGRAMS.items()]
          + [("combinators", n, p) for n, p in C.PROGRAMS.items()]
          + [("text", n, p) for n, p in T.PROGRAMS.items()]
          + [("types", n, p) for n, p in Y.PROGRAMS.items()]
          + [("sets", n, p) for n, p in Z.PROGRAMS.items()]
          + [("library", n, p) for n, p in B.PROGRAMS.items()]
          + [("pure", n, p) for n, p in P.PROGRAMS.items()]
          + [("symbols", n, p) for n, p in N.PROGRAMS.items()]
          + [("intern", n, p) for n, p in N.INTERN.items()]
          + [("numtext", n, p) for n, p in X.PROGRAMS.items()]
          + [("modes", n, p) for n, p in M.PROGRAMS.items()])
TABLES = {"words": (W.INTERPRETED, W.COMPILED),
          "combinators": (C.INTERPRETED, C.COMPILED),
          "text": (T.INTERPRETED, T.COMPILED),
          "types": (Y.INTERPRETED, Y.COMPILED),
          "sets": (Z.INTERPRETED, Z.COMPILED),
          "library": (B.INTERPRETED, B.COMPILED),
          "pure": (P.INTERPRETED, P.COMPILED),
          "symbols": (N.INTERPRETED, N.COMPILED),
          "intern": (N.INTERN_INTERPRETED, None),       # the interpreted form's alone
          "numtext": (X.INTERPRETED, X.COMPILED),
          "modes": (M.INTERPRETED, M.COMPILED)}


@pytest.mark.parametrize("module,name,text", PINNED)
def test_the_pinned_outcome_is_the_references(module, name, text):
    want = conform.reference(text)
    interp, comp = TABLES[module]
    assert conform.interpreted_outcome(interp[name][0]) == want, text
    if comp is not None:
        assert conform.compiled_outcome(comp[name][0]) == conform.compiled_expectation(want), text


#: where SKIlark and the reference part: program -> (the reference's
#: outcome, SKIlark's in both forms as the interpreted form reads it, why).
#: Since stage 6 a derived word checks its arguments' types as the
#: reference does (``typeof``), and a combinator its quotations before it
#: runs one, so one deviation is left, and the tree combinators of stage 7
#: share it.
DEVIATIONS = {
    "2 [0 =] [5] [pred] [first size] genrec": (
        ("RVal", [("N", 1), ("N", 5)]), ("RVal", [1, 11]),
        "genrec hands R2 [[[B] [T] [R1] R2] #genrecaux], the reference's own word; "
        "the derived genrec hands it a quotation that recurses through y"),
    "[1 2] [] [] treerec size popd": (
        ("RVal", [("N", 2)]), ("RVal", [3]),
        "treerec hands C [[[O] C] #treerecaux], the reference's own word; the derived "
        "treerec hands it a quotation that recurses through y"),
    "[1 2] [] [] [] treegenrec size popd": (
        ("RVal", [("N", 2)]), ("RVal", [3]),
        "treegenrec hands C [[[O1] [O2] C] #treegenrecaux], as treerec does"),
}


@pytest.mark.parametrize("text", sorted(DEVIATIONS))
def test_each_deviation_is_what_it_says(text):
    ref, ours, _ = DEVIATIONS[text]
    assert conform.reference(text) == ref, text
    assert interpreted({"p": text}).run("up")[0] == ours, text
    assert compiled({"p": text}).run("up")[0] == ours, text


# ------------------------------------------- the model against Joy's own

#: values worked by hand from the reference's definitions (factorial,
#: Fibonacci, the C division), the model's check on itself
DOCUMENTED = {
    "5 [1] [*] primrec": [("N", 120)],
    "[1 2 3] [dup *] map": [("L", (("N", 1), ("N", 4), ("N", 9)))],
    "3 [null] [succ] [dup pred] [*] linrec": [("N", 6)],
    "[1 2 3] 0 [+] fold": [("N", 6)],
    "[1 2 3 4] [2 rem 0 =] filter": [("L", (("N", 2), ("N", 4)))],
    "[1 2] [3 4] [+] infra": [("L", (("N", 1), ("N", 2))), ("L", (("N", 7),))],
    "1 2 3 stack": [("N", 1), ("N", 2), ("N", 3), ("L", (("N", 3), ("N", 2), ("N", 1)))],
    "6 [small] [] [pred dup pred] [+] binrec": [("N", 8)],
    "7 2 /": [("N", 3)],
    "-7 2 rem": [("N", -1)],
}


@pytest.mark.parametrize("text", sorted(DOCUMENTED))
def test_the_model_runs_joys_examples(text):
    assert joyref.Joy(conform.OWN).run(text) == ("RVal", DOCUMENTED[text])


# ------------------------------------------------------------- the fuzz

@pytest.mark.slow
def test_random_programs_differ_only_where_a_deviation_is_named():
    """Sixty random programs (``joyfuzz``, seed 1), interpreted: any
    difference from the reference is in a program that uses a word whose
    deviation is named above."""
    import joyfuzz
    progs = joyfuzz.programs(1, 60)
    run = interpreted({f"f{i}": p for i, p in enumerate(progs)})
    for i, p in enumerate(progs):
        got = conform.interpreted_outcome(run.run(f"uf{i}")[0])
        if got != conform.reference(p):
            assert joyfuzz.DEVIANT & set(p.replace("[", " ").replace("]", " ").split()), p
