"""Joy beyond the basis, stages 1 and 2 (PLAN.md §3, "Toward Joy in
full"): arithmetic and comparison on naturals, truth values, ``branch``
and ``ifte``, in both forms.  Every count was measured on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "w1": "3 4 *",
    "w2": "5 succ",
    "w3": "5 pred",
    "w4": "0 pred",
    "w5": "3 7 max",
    "w6": "3 7 min",
    "w7": "4 4 =",
    "w8": "2 3 <",
    "w9": "3 2 <",
    "w10": "2 3 >",
    "w11": "3 3 <=",
    "w12": "3 3 >=",
    "w13": "2 3 !=",
    "w14": "true false and",
    "w15": "true false or",
    "w16": "true not",
    "w17": "true true xor",
    "w18": "true false =",
    "w19": "true [1] [2] branch",
    "w20": "false [1] [2] branch",
    "w21": "1 [pop true] [2] [3] ifte",
    "w22": "4 [3 <] [1] [2] ifte",
    "w23": "5 fact",
    "w24": "1 true =",
    "w25": "1 [2] [3] branch",
    "w26": "true 1 *",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "w1": (("RVal", [12]), 2_127, 2_129),
    "w2": (("RVal", [6]), 1_311, 1_318),
    "w3": (("RVal", [4]), 1_306, 1_313),
    "w4": (("RErr", None), 1_245, 1_256),
    "w5": (("RVal", [7]), 2_121, 2_123),
    "w6": (("RVal", [3]), 2_119, 2_121),
    "w7": (("RVal", [True]), 2_055, 2_057),
    "w8": (("RVal", [True]), 2_115, 2_117),
    "w9": (("RVal", [False]), 2_115, 2_117),
    "w10": (("RVal", [False]), 2_786, 2_782),
    "w11": (("RVal", [True]), 3_422, 3_411),
    "w12": (("RVal", [True]), 2_750, 2_746),
    "w13": (("RVal", [True]), 2_667, 2_663),
    "w14": (("RVal", [False]), 1_929, 1_931),
    "w15": (("RVal", [True]), 1_927, 1_929),
    "w16": (("RVal", [False]), 1_214, 1_221),
    "w17": (("RVal", [False]), 2_574, 2_570),
    "w18": (("RVal", [False]), 1_962, 1_964),
    "w19": (("RVal", [1]), 3_408, 3_397),
    "w20": (("RVal", [2]), 3_402, 3_391),
    "w21": (("RVal", [1, 2]), 6_371, 6_318),
    "w22": (("RVal", [4, 2]), 6_904, 6_851),
    "w23": (("RVal", [120]), 100_268, 92_559),
    "w24": (("RErr", None), 1_923, 1_930),
    "w25": (("RErr", None), 2_620, 2_622),
    "w26": (("RErr", None), 2_041, 2_048),
}
COMPILED = {
    "w1": (("RVal", [12]), 301, 301),
    "w2": (("RVal", [6]), 111, 111),
    "w3": (("RVal", [4]), 127, 127),
    "w4": (("RErr", None), 113, 113),
    "w5": (("RVal", [7]), 301, 301),
    "w6": (("RVal", [3]), 301, 301),
    "w7": (("RVal", [True]), 255, 255),
    "w8": (("RVal", [True]), 301, 301),
    "w9": (("RVal", [False]), 301, 301),
    "w10": (("RVal", [False]), 419, 419),
    "w11": (("RVal", [True]), 547, 547),
    "w12": (("RVal", [True]), 429, 429),
    "w13": (("RVal", [True]), 364, 364),
    "w14": (("RVal", [False]), 239, 239),
    "w15": (("RVal", [True]), 239, 239),
    "w16": (("RVal", [False]), 104, 104),
    "w17": (("RVal", [False]), 343, 343),
    "w18": (("RVal", [False]), 234, 234),
    "w19": (("RVal", [1]), 606, 620),
    "w20": (("RVal", [2]), 600, 614),
    "w21": (("RVal", [1, 2]), 1_079, 1_107),
    "w22": (("RVal", [4, 2]), 1_485, 1_513),
    "w23": (("RVal", [120]), 23_606, 22_707),
    "w24": (("RErr", None), 231, 231),
    "w25": (("RErr", None), 379, 379),
    "w26": (("RErr", None), 289, 289),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.fixture(scope="module")
def comp():
    return compiled(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_words(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_words(comp, name):
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_ifte_runs_its_test_then_restores_the_stack():
    """``[B] [T] [F] ifte`` runs B for its truth value alone: what B did to
    the stack is undone before T or F runs (w21 pops the 1, which comes
    back)."""
    assert INTERPRETED["w21"][0] == COMPILED["w21"][0] == ("RVal", [1, 2])


def test_a_program_without_truth_values_keeps_its_compiled_kernel():
    """The compiled form carries ``Logical`` items only for a program that
    uses a truth word, so the terms of every other program, among them
    zk's verifiers, are what they were."""
    from skilark import joy
    assert "Logical logical" not in joy.compiled({"p": "3 4 * 5 max"})
    assert "Logical logical" in joy.compiled({"p": "3 4 <"})
    assert "Logical logical" in joy.compiled({"p": "[true] i"})


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "x y * == y x *":               ("3 4 *", "4 3 *"),
    "x succ pred == x":             ("5 succ pred", "5"),
    "x y max == y x max":           ("3 7 max", "7 3 max"),
    "x y min == y x min":           ("3 7 min", "7 3 min"),
    "x y < == y x >":               ("2 3 <", "3 2 >"),
    "x y != == x y = not":          ("2 3 !=", "2 3 = not"),
    "b not not == b":               ("false not not", "false"),
    "a b and == b a and":           ("true false and", "false true and"),
    "a b or == b a or":             ("true false or", "false true or"),
    "a b and not == a not b not or": ("true false and not", "true not false not or"),
    "true [T] [F] branch == T":     ("true [1 2 +] [5] branch", "1 2 +"),
    "false [T] [F] branch == F":    ("false [1 2 +] [5] branch", "5"),
    "x [P] [T] [F] ifte == x x P [T] [F] branch":
        ("4 [3 <] [1] [2] ifte", "4 dup 3 < [1] [2] branch"),
}
LAW_PROGRAMS = {f"l{i}{side}": text
                for i, (l, r) in enumerate(LAWS.values())
                for side, text in (("L", l), ("R", r))}


@pytest.fixture(scope="module", params=["interpreted", "compiled"])
def laws(request):
    return (interpreted if request.param == "interpreted" else compiled)(LAW_PROGRAMS)


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_in_both_forms(laws, i):
    left, right = laws.run(f"ul{i}L")[0], laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(LAWS)[i]
