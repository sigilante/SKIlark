"""Phase 3: the kernel's loop and fuel in variants (``skilark.variants``),
pinned on the phase-2 programs.  Every count is host contractions on
skijack 0.2.1; ``PLAN.md`` §3 records the tables and the decisions.
Church fuel is the kernel's; the Scott fuels are what it had before.
"""

import pytest

from skilark import Run, joy
from skilark import variants as V
from skilark.joy import DEFINITIONS, _programs, datum, nat
from test_modes import COMPILED, INTERPRETED

#: (loop, fuel) -> fuelled count per program, p1 .. p8.  The splice with
#: computed fuel is the kernel before Church fuel, and its row is the
#: counts phase 2 pinned then.
FUELLED = {
    ("splice", "computed"):    (9_276, 9_291, 11_601, 14_030, 7_820, 3_385, 110_770, 173_744),
    ("splice", "literal"):     (2_298, 2_313, 2_973, 3_725, 1_663, 325, 35_171, 54_449),
    ("splice", "church"):      (2_003, 2_018, 2_561, 3_197, 1_425, 290, 29_641, 44_647),
    ("stack", "computed"):     (10_475, 11_313, 14_090, 17_850, 8_741, 3_575, 138_784, 217_546),
    ("stack", "literal"):      (3_497, 3_514, 4_641, 5_894, 2_584, 515, 48_646, 75_089),
    ("sequenced", "computed"): (9_980, 10_802, 12_115, 15_777, 8_340, 3_496, 126_765, 196_614),
    ("sequenced", "literal"):  (3_002, 3_009, 3_487, 4_561, 2_183, 436, 40_258, 61_474),
}
#: loop -> unfuelled count per program
UNFUELLED = {
    "splice":    (2_014, 2_029, 2_589, 3_250, 1_429, 276, 31_890, 49_568),
    "stack":     (2_978, 2_914, 3_858, 4_858, 2_156, 428, 41_770, 64_809),
    "sequenced": (2_014, 1_958, 2_299, 2_967, 1_429, 276, 28_042, 43_256),
}
#: fuel -> the compiled form's fuelled count per program; computed is the
#: compiled form before Church fuel
COMPILED_FUELLED = {
    "computed": (493, 3_164, 3_254, 6_074, 264, 6, 40_594, 63_921),
    "literal":  (493, 667, 757, 1_080, 264, 6, 15_414, 23_603),
    "church":   (493, 550, 640, 848, 264, 6, 11_508, 17_413),
}


@pytest.mark.parametrize("loop,fuel", list(V.INTERPRETED))
def test_every_loop_and_fuel_gives_the_kernels_outcomes(loop, fuel):
    t = V.table(V.interpreted(loop, fuel))
    for i, p in enumerate(V.PROGRAMS):
        outcome, n, u = t[p]
        assert outcome == INTERPRETED[p][0], (p, outcome)
        assert n == FUELLED[(loop, fuel)][i], (p, n)
        if fuel == "computed":
            assert u == UNFUELLED[loop][i], (p, u)


def test_the_splice_with_church_fuel_is_the_kernel():
    t = V.table(V.interpreted("splice", "church"))
    assert {p: (o, n) for p, (o, n, u) in t.items()} == \
        {p: (o, n) for p, (o, u, n) in INTERPRETED.items()}
    t = V.table(V.compiled("church"))
    assert {p: (o, n) for p, (o, n, u) in t.items()} == \
        {p: (o, n) for p, (o, u, n) in COMPILED.items()}


@pytest.mark.parametrize("fuel", list(COMPILED_FUELLED))
def test_the_compiled_forms_fuel(fuel):
    t = V.table(V.compiled(fuel))
    for i, p in enumerate(V.PROGRAMS):
        outcome, n, u = t[p]
        assert (outcome, u) == (COMPILED[p][0], COMPILED[p][1]), p
        assert n == COMPILED_FUELLED[fuel][i], (p, n)


def test_church_fuel_times_out_where_scott_fuel_does():
    """Church fuel ``n`` and the Scott numeral ``n`` stop a run at the
    same word: one unit per word, and one at ``Done``."""
    progs = {"p1": "1 2 + dup +", "p7": "3 sumto", "loop": "[dup i] dup i"}
    ns = (5, 6, 65, 66)
    src = [joy._kernel(), V.SCOTT]
    src += [V.church(n) + f"f{n} := {nat(n)}\n" for n in ns]
    for name, prog in _programs(progs, DEFINITIONS).items():
        src.append(f"p{name} := {datum(prog)}\n")
        for n in ns:
            src.append(f"s{name}x{n} := execS f{n} p{name} Empty\n")
            src.append(f"c{name}x{n} := exec c{n} p{name} Empty\n")
    r = Run("".join(src), "interpreted")
    seen = {}
    for name in progs:
        for n in ns:
            a, b = r.run(f"s{name}x{n}")[0], r.run(f"c{name}x{n}")[0]
            assert a == b, (name, n, a, b)
            seen[(name, n)] = a[0]
    # 1 2 + dup + is five words; 3 sumto is 65; the loop never ends
    assert [seen[("p1", n)] for n in ns] == ["RTime", "RVal", "RVal", "RVal"]
    assert [seen[("p7", n)] for n in ns] == ["RTime", "RTime", "RTime", "RVal"]
    assert {seen[("loop", n)] for n in ns} == {"RTime"}


def test_the_splice_costs_a_constant_per_word_copied():
    """``[P] i`` against ``P``, unfuelled: the splice copies P once, at
    100 to 150 contractions a word on top of the 330 to 400 that run it; the
    sequenced loop's ``Do`` costs about the same at any length."""
    progs = {}
    for n in (5, 20, 80):
        body = " ".join(["1 pop"] * n)
        progs[f"q{n}"], progs[f"f{n}"] = f"[{body}] i", body
    got = {}
    for loop in ("splice", "sequenced", "stack"):
        r = V.interpreted(loop, "computed", progs)
        got[loop] = tuple(r.run("u" + p)[1] for p in progs)
    assert got == {
        "splice":    (4_677, 3_269, 17_727, 13_604, 87_927, 63_944),
        "sequenced": (4_050, 3_269, 14_445, 13_604, 65_025, 63_944),
        "stack":     (6_105, 4_947, 21_465, 20_217, 91_905, 90_297),
    }
