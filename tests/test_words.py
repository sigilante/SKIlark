"""Joy beyond the basis (PLAN.md §3, "Toward Joy in full"): stage 1,
arithmetic and comparison, on integers since stage 1b; stage 2, truth
values, ``branch`` and ``ifte``; stage 3, quotations as lists, with words
as symbols; in both forms.  Every count was measured on skijack 0.2.1.
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
    "w49": "[1 2 3] first",
    "w50": "[1 2 3] rest",
    "w51": "[1 2 3] uncons",
    "w52": "[1 2 3] unswons",
    "w53": "[] null",
    "w54": "[1] null",
    "w55": "0 null",
    "w56": "[1] small",
    "w57": "[1 2] small",
    "w58": "1 small",
    "w59": "2 small",
    "w60": "[1 2 3] size",
    "w61": "[] size",
    "w62": "[dup +] first",
    "w63": "3 [dup +] first unit i",
    "w64": "[1 2] [3 4] concat size",
    "w65": "[1 2] [3 4] concat 2 at",
    "w66": "[1 2 3 4] 2 take",
    "w67": "[1 2 3 4] 2 drop",
    "w68": "[1 2] 5 take",
    "w69": "[1 2] 5 drop",
    "w70": "[] first",
    "w71": "[dup] first [dup] first =",
    "w72": "[dup] first [swap] first =",
    "w73": "[1 2] 0 swons",
    "w74": "[[1 2] 3] first size",
    "w75": "1 [2 3] of",
    "w76": "[2 3] 1 at",
    "w77": "[1 2] [3] cat uncons",
    "w78": "[true 1] first",
    "w79": "[] [1] cat first",
    "w80": "[1 2] [] cat size",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "w1": (("RVal", [12]), 2_091, 2_093),
    "w2": (("RVal", [6]), 2_095, 2_097),
    "w3": (("RVal", [4]), 2_093, 2_095),
    "w4": (("RVal", [-1]), 2_093, 2_095),
    "w5": (("RVal", [7]), 12_266, 12_069),
    "w6": (("RVal", [3]), 11_555, 11_378),
    "w7": (("RVal", [True]), 2_001, 2_003),
    "w8": (("RVal", [True]), 2_083, 2_085),
    "w9": (("RVal", [False]), 2_083, 2_085),
    "w10": (("RVal", [False]), 2_716, 2_712),
    "w11": (("RVal", [True]), 5_723, 5_685),
    "w12": (("RVal", [True]), 5_086, 5_058),
    "w13": (("RVal", [True]), 4_923, 4_895),
    "w14": (("RVal", [False]), 9_384, 9_261),
    "w15": (("RVal", [True]), 10_644, 10_486),
    "w16": (("RVal", [False]), 3_296, 3_285),
    "w17": (("RVal", [False]), 4_670, 4_642),
    "w18": (("RVal", [False]), 1_912, 1_914),
    "w19": (("RVal", [1]), 3_314, 3_303),
    "w20": (("RVal", [2]), 3_308, 3_297),
    "w21": (("RVal", [1, 2]), 6_294, 6_241),
    "w22": (("RVal", [4, 2]), 6_932, 6_879),
    "w23": (("RVal", [120]), 107_155, 98_811),
    "w24": (("RErr", None), 1_871, 1_878),
    "w25": (("RErr", None), 2_564, 2_566),
    "w26": (("RErr", None), 2_007, 2_014),
    "w27": (("RVal", [-2]), 2_093, 2_095),
    "w28": (("RVal", [3]), 2_726, 2_722),
    "w29": (("RVal", [3]), 7_199, 7_134),
    "w30": (("RVal", [-1]), 6_118, 6_065),
    "w31": (("RVal", [0]), 9_471, 9_364),
    "w32": (("RVal", [1]), 9_481, 9_374),
    "w33": (("RVal", [3]), 2_142, 2_144),
    "w34": (("RVal", [-3]), 2_142, 2_144),
    "w35": (("RVal", [-3]), 2_138, 2_140),
    "w36": (("RVal", [-1]), 2_140, 2_142),
    "w37": (("RVal", [1]), 2_136, 2_138),
    "w38": (("RErr", None), 2_062, 2_069),
    "w39": (("RVal", [-6]), 2_091, 2_093),
    "w40": (("RVal", [6]), 2_091, 2_093),
    "w41": (("RVal", [True]), 2_083, 2_085),
    "w42": (("RVal", [True]), 2_083, 2_085),
    "w43": (("RVal", [0]), 2_095, 2_097),
    "w44": (("RVal", [True]), 2_001, 2_003),
    "w45": (("RVal", [1]), 12_036, 11_839),
    "w46": (("RVal", [-1]), 2_095, 2_097),
    "w47": (("RVal", [[("Lit", -1)]]), 1_160, 1_167),
    "w48": (("RVal", [10]), 87_605, 81_756),
    "w49": (("RVal", [1]), 1_800, 1_802),
    "w50": (("RVal", [[("Lit", 2), ("Lit", 3)]]), 2_438, 2_434),
    "w51": (("RVal", [1, [("Lit", 2), ("Lit", 3)]]), 1_243, 1_250),
    "w52": (("RVal", [[("Lit", 2), ("Lit", 3)], 1]), 1_878, 1_880),
    "w53": (("RVal", [True]), 1_206, 1_213),
    "w54": (("RVal", [False]), 1_206, 1_213),
    "w55": (("RVal", [True]), 1_210, 1_217),
    "w56": (("RVal", [True]), 1_204, 1_211),
    "w57": (("RVal", [False]), 1_204, 1_211),
    "w58": (("RVal", [True]), 1_208, 1_215),
    "w59": (("RVal", [False]), 1_208, 1_215),
    "w60": (("RVal", [3]), 55_717, 52_967),
    "w61": (("RVal", [0]), 14_886, 14_631),
    "w62": (("RVal", [("Sym", "Dup")]), 1_800, 1_802),
    "w63": (("RVal", [3, 3]), 4_391, 4_363),
    "w64": (("RVal", [4]), 71_768, 67_426),
    "w65": (("RVal", [3]), 99_041, 90_954),
    "w66": (("RVal", [[("Lit", 1), ("Lit", 2)]]), 95_845, 88_260),
    "w67": (("RVal", [[("Lit", 3), ("Lit", 4)]]), 95_658, 88_073),
    "w68": (("RVal", [[("Lit", 1), ("Lit", 2)]]), 97_347, 89_513),
    "w69": (("RVal", [[]]), 97_160, 89_326),
    "w70": (("RErr", None), 1_160, 1_171),
    "w71": (("RVal", [True]), 4_545, 4_517),
    "w72": (("RVal", [False]), 4_543, 4_515),
    "w73": (("RVal", [[("Lit", 0), ("Lit", 1), ("Lit", 2)]]), 2_495, 2_491),
    "w74": (("RVal", [2]), 43_382, 41_633),
    "w75": (("RVal", [3]), 63_213, 59_591),
    "w76": (("RVal", [3]), 62_509, 58_972),
    "w77": (("RVal", [1, [("Lit", 2), ("Lit", 3)]]), 2_666, 2_662),
    "w78": (("RVal", [True]), 1_800, 1_802),
    "w79": (("RVal", [1]), 3_196, 3_185),
    "w80": (("RVal", [2]), 43_546, 41_797),
}
COMPILED = {
    "w1": (("RVal", [12]), 343, 343),
    "w2": (("RVal", [6]), 343, 343),
    "w3": (("RVal", [4]), 343, 343),
    "w4": (("RVal", [-1]), 343, 343),
    "w5": (("RVal", [7]), 6_697, 6_739),
    "w6": (("RVal", [3]), 6_578, 6_620),
    "w7": (("RVal", [True]), 283, 283),
    "w8": (("RVal", [True]), 343, 343),
    "w9": (("RVal", [False]), 343, 343),
    "w10": (("RVal", [False]), 461, 461),
    "w11": (("RVal", [True]), 2_729, 2_743),
    "w12": (("RVal", [True]), 2_609, 2_623),
    "w13": (("RVal", [True]), 2_472, 2_486),
    "w14": (("RVal", [False]), 6_141, 6_183),
    "w15": (("RVal", [True]), 6_215, 6_257),
    "w16": (("RVal", [False]), 1_997, 2_011),
    "w17": (("RVal", [False]), 2_287, 2_301),
    "w18": (("RVal", [False]), 262, 262),
    "w19": (("RVal", [1]), 1_987, 2_001),
    "w20": (("RVal", [2]), 1_981, 1_995),
    "w21": (("RVal", [1, 2]), 3_796, 3_824),
    "w22": (("RVal", [4, 2]), 4_280, 4_308),
    "w23": (("RVal", [120]), 94_672, 93_773),
    "w24": (("RErr", None), 259, 259),
    "w25": (("RErr", None), 444, 444),
    "w26": (("RErr", None), 331, 331),
    "w27": (("RVal", [-2]), 343, 343),
    "w28": (("RVal", [3]), 461, 461),
    "w29": (("RVal", [3]), 2_882, 2_896),
    "w30": (("RVal", [-1]), 2_546, 2_560),
    "w31": (("RVal", [0]), 4_721, 4_732),
    "w32": (("RVal", [1]), 4_795, 4_806),
    "w33": (("RVal", [3]), 387, 387),
    "w34": (("RVal", [-3]), 387, 387),
    "w35": (("RVal", [-3]), 383, 383),
    "w36": (("RVal", [-1]), 387, 387),
    "w37": (("RVal", [1]), 383, 383),
    "w38": (("RErr", None), 363, 363),
    "w39": (("RVal", [-6]), 343, 343),
    "w40": (("RVal", [6]), 343, 343),
    "w41": (("RVal", [True]), 343, 343),
    "w42": (("RVal", [True]), 343, 343),
    "w43": (("RVal", [0]), 343, 343),
    "w44": (("RVal", [True]), 283, 283),
    "w45": (("RVal", [1]), 6_467, 6_509),
    "w46": (("RVal", [-1]), 343, 343),
    "w47": (("RVal", [("quot", ("RVal", [-1]))]), 82, 82),
    "w48": (("RVal", [10]), 77_815, 77_192),
    "w49": (("RVal", [1]), 702, 702),
    "w50": (("RVal", [("quot", ("RVal", [2, 3]))]), 823, 823),
    "w51": (("RVal", [1, ("quot", ("RVal", [2, 3]))]), 625, 625),
    "w52": (("RVal", [("quot", ("RVal", [2, 3])), 1]), 744, 744),
    "w53": (("RVal", [True]), 118, 118),
    "w54": (("RVal", [False]), 118, 118),
    "w55": (("RVal", [True]), 120, 120),
    "w56": (("RVal", [True]), 118, 118),
    "w57": (("RVal", [False]), 118, 118),
    "w58": (("RVal", [True]), 120, 120),
    "w59": (("RVal", [False]), 120, 120),
    "w60": (("RVal", [3]), 56_932, 56_598),
    "w61": (("RVal", [0]), 13_859, 13_844),
    "w62": (("RVal", [("Sym", "Dup")]), 696, 696),
    "w63": (("RVal", [3, 3]), 4_295, 4_306),
    "w64": (("RVal", [4]), 83_340, 82_847),
    "w65": (("RVal", [3]), 86_783, 86_409),
    "w66": (("RVal", [("quot", ("RVal", [1, 2]))]), 73_831, 73_457),
    "w67": (("RVal", [("quot", ("RVal", [3, 4]))]), 73_831, 73_457),
    "w68": (("RVal", [("quot", ("RVal", [1, 2]))]), 74_152, 73_778),
    "w69": (("RVal", [("quot", ("RVal", []))]), 74_152, 73_778),
    "w70": (("RErr", None), 654, 654),
    "w71": (("RVal", [True]), 1_733, 1_733),
    "w72": (("RVal", [False]), 1_681, 1_681),
    "w73": (("RVal", [("quot", ("RVal", [0, 1, 2]))]), 320, 320),
    "w74": (("RVal", [2]), 43_250, 43_060),
    "w75": (("RVal", [3]), 48_655, 48_475),
    "w76": (("RVal", [3]), 48_533, 48_353),
    "w77": (("RVal", [1, ("quot", ("RVal", [2, 3]))]), 2_685, 2_685),
    "w78": (("RVal", [True]), 680, 680),
    "w79": (("RVal", [1]), 3_262, 3_262),
    "w80": (("RVal", [2]), 52_321, 52_131),
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
    assert "int    ===" not in joy.compiled({"p": "3 4 * 5 +"})
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


def test_a_word_in_a_quotation_is_a_symbol():
    """Joy's ``[dup +] first`` is the symbol ``dup``, which runs when it is
    consed back into a quotation and the quotation is run, and ``=`` tells
    two symbols apart by name."""
    assert INTERPRETED["w62"][0] == COMPILED["w62"][0] == ("RVal", [("Sym", "Dup")])
    assert INTERPRETED["w63"][0] == COMPILED["w63"][0] == ("RVal", [3, 3])
    assert [INTERPRETED[w][0][1] for w in ("w71", "w72")] == [[True], [False]]


def test_only_a_list_reading_program_carries_symbols():
    """A compiled program has ``Sym`` items, and the views of its static
    quotations, only when it reads a quotation as a list."""
    from skilark import joy
    assert "Sym sym" not in joy.compiled({"p": "[1 2] i 3 +"})
    assert "Sym sym" in joy.compiled({"p": "[1 2] first"})
    assert "Sym sym" in joy.compiled({"p": "[1 2] size"})


def test_a_program_without_truth_values_keeps_its_compiled_kernel():
    """The compiled form carries ``Logical`` items only for a program that
    uses a truth word, so the terms of every other program, among them
    zk's verifiers, are what they were."""
    from skilark import joy
    assert "Logical logical" not in joy.compiled({"p": "3 4 * 5 +"})
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
    "[x A] first == x":             ("[7 8 9] first", "7"),
    "x A cons uncons == x A":       ("1 [2 3] cons uncons", "1 [2 3]"),
    "A B concat size == A size B size +": ("[1 2] [3] concat size", "[1 2] size [3] size +"),
    "A n take A n drop concat == A": ("[1 2 3] 1 take [1 2 3] 1 drop concat", "[1 2 3]"),
    "A unswons swons == A":         ("[4 5] unswons swons", "[4 5]"),
    "[] null == true":              ("[] null", "true"),
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
