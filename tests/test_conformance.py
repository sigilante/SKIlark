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
import test_words as W
from skilark import compiled, interpreted

#: every program whose outcome some module pins: (module, name, text)
PINNED = ([("words", n, p) for n, p in W.PROGRAMS.items()]
          + [("combinators", n, p) for n, p in C.PROGRAMS.items()]
          + [("modes", n, p) for n, p in M.PROGRAMS.items()])
TABLES = {"words": (W.INTERPRETED, W.COMPILED),
          "combinators": (C.INTERPRETED, C.COMPILED),
          "modes": (M.INTERPRETED, M.COMPILED)}


@pytest.mark.parametrize("module,name,text", PINNED)
def test_the_pinned_outcome_is_the_references(module, name, text):
    want = conform.reference(text)
    interp, comp = TABLES[module]
    assert conform.interpreted_outcome(interp[name][0]) == want, text
    assert conform.compiled_outcome(comp[name][0]) == conform.compiled_expectation(want), text


#: where SKIlark and the reference part: program -> (the reference's
#: outcome, SKIlark's in both forms as the interpreted form reads it, why).
#: A derived word cannot see its argument's kind: Joy has a test for it
#: (``logical``, ``integer``, ``list`` ...), which the kernel does not
#: have yet; and a derived combinator checks a quotation when it runs it.
DEVIATIONS = {
    "[1] not": (("RErr", None), ("RVal", [False]),
                "not takes a number or truth value; the derived not takes any value"),
    "true 5 and": (("RErr", None), ("RVal", [True]),
                   "and takes two values of one kind; the derived and cannot compare kinds"),
    "true 1 xor": (("RErr", None), ("RVal", [False]),
                   "xor takes two values of one kind"),
    "3 true max": (("RErr", None), ("RVal", [3]),
                   "max takes two numbers of one kind"),
    "true false max": (("RVal", [("N", 1)]), ("RVal", [True]),
                       "max of truth values is an integer in the reference"),
    "true succ": (("RVal", [("N", 2)]), ("RErr", None),
                  "succ of a truth value is an integer; the derived succ is 1 +, "
                  "which takes no truth value"),
    "[1 2] true take": (("RVal", [("L", (("N", 1),))]), ("RErr", None),
                        "take's index may be a truth value in the reference"),
    "1 [pop true] [5] 7 tailrec": (("RErr", None), ("RVal", [1, 5]),
                                   "tailrec checks its three quotations at once; the derived "
                                   "tailrec checks R1 only when it runs it"),
    "2 [0 =] [5] [pred] [first size] genrec": (
        ("RVal", [("N", 1), ("N", 5)]), ("RVal", [1, 11]),
        "genrec hands R2 [[[B] [T] [R1] R2] #genrecaux], the reference's own word; "
        "the derived genrec hands it a quotation that recurses through y"),
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
