"""Joy beyond the basis (PLAN.md §3, "Toward Joy in full"): stage 1,
arithmetic and comparison, on integers since stage 1b; stage 2, truth
values, ``branch`` and ``ifte``; in both forms.  Every count was measured
on skijack 0.2.1.
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
    "w27": "3 5 -",
    "w28": "-3 neg",
    "w29": "-3 abs",
    "w30": "-3 sign",
    "w31": "0 sign",
    "w32": "4 sign",
    "w33": "7 2 /",
    "w34": "-7 2 /",
    "w35": "7 -2 /",
    "w36": "-7 2 rem",
    "w37": "7 -2 rem",
    "w38": "7 0 /",
    "w39": "-2 3 *",
    "w40": "-2 -3 *",
    "w41": "-2 3 <",
    "w42": "-3 -2 <",
    "w43": "-1 succ",
    "w44": "-5 -5 =",
    "w45": "-1 1 max",
    "w46": "1 -2 +",
    "w47": "-1 unit",
    "w48": "4 sumto",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "w1": (("RVal", [12]), 2_253, 2_255),
    "w2": (("RVal", [6]), 1_389, 1_396),
    "w3": (("RVal", [4]), 1_387, 1_394),
    "w4": (("RVal", [-1]), 1_387, 1_394),
    "w5": (("RVal", [7]), 2_243, 2_245),
    "w6": (("RVal", [3]), 2_241, 2_243),
    "w7": (("RVal", [True]), 2_177, 2_179),
    "w8": (("RVal", [True]), 2_237, 2_239),
    "w9": (("RVal", [False]), 2_237, 2_239),
    "w10": (("RVal", [False]), 2_946, 2_942),
    "w11": (("RVal", [True]), 3_616, 3_605),
    "w12": (("RVal", [True]), 2_906, 2_902),
    "w13": (("RVal", [True]), 2_823, 2_819),
    "w14": (("RVal", [False]), 2_039, 2_041),
    "w15": (("RVal", [True]), 2_037, 2_039),
    "w16": (("RVal", [False]), 1_286, 1_293),
    "w17": (("RVal", [False]), 2_718, 2_714),
    "w18": (("RVal", [False]), 2_072, 2_074),
    "w19": (("RVal", [1]), 3_612, 3_601),
    "w20": (("RVal", [2]), 3_606, 3_595),
    "w21": (("RVal", [1, 2]), 6_820, 6_767),
    "w22": (("RVal", [4, 2]), 7_376, 7_323),
    "w23": (("RVal", [120]), 106_228, 98_519),
    "w24": (("RErr", None), 2_039, 2_046),
    "w25": (("RErr", None), 2_786, 2_788),
    "w26": (("RErr", None), 2_161, 2_168),
    "w27": (("RVal", [-2]), 2_255, 2_257),
    "w28": (("RVal", [3]), 2_964, 2_960),
    "w29": (("RVal", [3]), 7_721, 7_656),
    "w30": (("RVal", [-1]), 6_646, 6_593),
    "w31": (("RVal", [0]), 10_153, 10_046),
    "w32": (("RVal", [1]), 10_163, 10_056),
    "w33": (("RVal", [3]), 2_304, 2_306),
    "w34": (("RVal", [-3]), 2_304, 2_306),
    "w35": (("RVal", [-3]), 2_300, 2_302),
    "w36": (("RVal", [-1]), 2_302, 2_304),
    "w37": (("RVal", [1]), 2_298, 2_300),
    "w38": (("RErr", None), 2_224, 2_231),
    "w39": (("RVal", [-6]), 2_253, 2_255),
    "w40": (("RVal", [6]), 2_253, 2_255),
    "w41": (("RVal", [True]), 2_237, 2_239),
    "w42": (("RVal", [True]), 2_237, 2_239),
    "w43": (("RVal", [0]), 1_389, 1_396),
    "w44": (("RVal", [True]), 2_177, 2_179),
    "w45": (("RVal", [1]), 2_243, 2_245),
    "w46": (("RVal", [-1]), 2_257, 2_259),
    "w47": (("RVal", [[("Lit", -1)]]), 1_320, 1_327),
    "w48": (("RVal", [10]), 87_572, 82_149),
}
COMPILED = {
    "w1": (("RVal", [12]), 301, 301),
    "w2": (("RVal", [6]), 131, 131),
    "w3": (("RVal", [4]), 131, 131),
    "w4": (("RVal", [-1]), 131, 131),
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
    "w19": (("RVal", [1]), 702, 716),
    "w20": (("RVal", [2]), 696, 710),
    "w21": (("RVal", [1, 2]), 1_271, 1_299),
    "w22": (("RVal", [4, 2]), 1_717, 1_745),
    "w23": (("RVal", [120]), 28_832, 27_933),
    "w24": (("RErr", None), 231, 231),
    "w25": (("RErr", None), 379, 379),
    "w26": (("RErr", None), 289, 289),
    "w27": (("RVal", [-2]), 301, 301),
    "w28": (("RVal", [3]), 419, 419),
    "w29": (("RVal", [3]), 1_511, 1_525),
    "w30": (("RVal", [-1]), 1_215, 1_229),
    "w31": (("RVal", [0]), 2_109, 2_120),
    "w32": (("RVal", [1]), 2_151, 2_162),
    "w33": (("RVal", [3]), 345, 345),
    "w34": (("RVal", [-3]), 345, 345),
    "w35": (("RVal", [-3]), 341, 341),
    "w36": (("RVal", [-1]), 345, 345),
    "w37": (("RVal", [1]), 341, 341),
    "w38": (("RErr", None), 321, 321),
    "w39": (("RVal", [-6]), 301, 301),
    "w40": (("RVal", [6]), 301, 301),
    "w41": (("RVal", [True]), 301, 301),
    "w42": (("RVal", [True]), 301, 301),
    "w43": (("RVal", [0]), 131, 131),
    "w44": (("RVal", [True]), 255, 255),
    "w45": (("RVal", [1]), 301, 301),
    "w46": (("RVal", [-1]), 301, 301),
    "w47": (("RVal", [("quot", ("RVal", [-1]))]), 82, 82),
    "w48": (("RVal", [10]), 23_672, 23_049),
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


def test_a_program_that_cannot_go_negative_computes_on_naturals():
    """Negatives come only from ``- pred / rem`` and negative literals, so a
    compiled program without them computes on naturals, with the same
    answers; zk's verifiers are such programs."""
    from skilark import joy
    assert "int    ===" not in joy.compiled({"p": "3 4 * 5 max"})
    assert "int    ===" in joy.compiled({"p": "3 5 -"})
    assert "int    ===" in joy.compiled({"p": "[-1] i"})
    assert "int    ===" in joy.compiled({"p": "4 sumto"})      # sumto uses pred


def test_ifz_has_left_the_kernel():
    """``ifz``, the Scott eliminator of a natural, is not Joy: the
    interpreted form refuses it, and the compiled form keeps it only for a
    program on naturals."""
    from skilark import joy
    with pytest.raises(ValueError, match="not a Joy word"):
        joy.interpreted({"p": "1 [2] [3] ifz"})
    assert "wIfz" in joy.compiled({"p": "1 [2] [3] ifz"})
    with pytest.raises(ValueError, match="ifz takes naturals"):
        joy.compiled({"p": "1 pred [2] [3] ifz"})


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
    "x y - == x y neg +":           ("3 5 -", "3 5 neg +"),
    "x neg neg == x":               ("-4 neg neg", "-4"),
    "x pred succ == x":             ("-2 pred succ", "-2"),
    "x y / y * x y rem + == x":     ("-7 2 / 2 * -7 2 rem +", "-7"),
    "x abs == x sign x *":          ("-3 abs", "-3 sign -3 *"),
    "x y < == x y - 0 <":           ("-3 2 <", "-3 2 - 0 <"),
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
