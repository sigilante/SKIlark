"""Joy beyond the basis (PLAN.md §3, "Toward Joy in full"): stage 1,
arithmetic and comparison, on integers since stage 1b; stage 2, truth
values, ``branch`` and ``ifte``; stage 3, quotations as lists, with words
as symbols; in both forms.  Since stage 4 the words behave as the
reference implementation's (``test_conformance``): a test takes any value
as a truth value and ``=`` compares across kinds, so ``1 true =`` is true
and ``1 [2] [3] branch`` runs ``[2]``.  Every count was measured on
skijack 0.2.1.
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
    "w1": (('RVal', [12]), 2_577, 2_579),
    "w2": (('RVal', [6]), 2_581, 2_583),
    "w3": (('RVal', [4]), 2_579, 2_581),
    "w4": (('RVal', [-1]), 2_579, 2_581),
    "w5": (('RVal', [7]), 14_960, 14_768),
    "w6": (('RVal', [3]), 14_091, 13_919),
    "w7": (('RVal', [True]), 2_269, 2_271),
    "w8": (('RVal', [True]), 2_267, 2_269),
    "w9": (('RVal', [False]), 2_267, 2_269),
    "w10": (('RVal', [False]), 15_627, 15_410),
    "w11": (('RVal', [True]), 14_132, 13_960),
    "w12": (('RVal', [True]), 6_010, 5_982),
    "w13": (('RVal', [True]), 5_965, 5_937),
    "w14": (('RVal', [False]), 18_248, 17_967),
    "w15": (('RVal', [True]), 19_863, 19_531),
    "w16": (('RVal', [False]), 4_058, 4_047),
    "w17": (('RVal', [False]), 5_863, 5_835),
    "w18": (('RVal', [False]), 2_235, 2_237),
    "w19": (('RVal', [1]), 4_075, 4_064),
    "w20": (('RVal', [2]), 4_069, 4_058),
    "w21": (('RVal', [1, 2]), 7_731, 7_678),
    "w22": (('RVal', [4, 2]), 8_226, 8_173),
    "w23": (('RVal', [120]), 133_976, 124_964),
    "w24": (('RVal', [True]), 2_252, 2_254),
    "w25": (('RVal', [2]), 4_128, 4_117),
    "w26": (('RErr', None), 2_494, 2_501),
    "w27": (('RVal', [-2]), 2_579, 2_581),
    "w28": (('RVal', [3]), 3_370, 3_366),
    "w29": (('RVal', [3]), 11_927, 11_809),
    "w30": (('RVal', [-1]), 10_683, 10_581),
    "w31": (('RVal', [0]), 14_416, 14_244),
    "w32": (('RVal', [1]), 14_658, 14_486),
    "w33": (('RVal', [3]), 2_628, 2_630),
    "w34": (('RVal', [-3]), 2_628, 2_630),
    "w35": (('RVal', [-3]), 2_624, 2_626),
    "w36": (('RVal', [-1]), 2_626, 2_628),
    "w37": (('RVal', [1]), 2_622, 2_624),
    "w38": (('RErr', None), 2_548, 2_555),
    "w39": (('RVal', [-6]), 2_577, 2_579),
    "w40": (('RVal', [6]), 2_577, 2_579),
    "w41": (('RVal', [True]), 2_267, 2_269),
    "w42": (('RVal', [True]), 2_267, 2_269),
    "w43": (('RVal', [0]), 2_581, 2_583),
    "w44": (('RVal', [True]), 2_269, 2_271),
    "w45": (('RVal', [1]), 14_744, 14_552),
    "w46": (('RVal', [-1]), 2_581, 2_583),
    "w47": (('RVal', [[('Lit', -1)]]), 1_482, 1_489),
    "w48": (('RVal', [10]), 109_245, 102_948),
    "w49": (('RVal', [1]), 2_281, 2_283),
    "w50": (('RVal', [[('Lit', 2), ('Lit', 3)]]), 3_077, 3_073),
    "w51": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 1_566, 1_573),
    "w52": (('RVal', [[('Lit', 2), ('Lit', 3)], 1]), 2_359, 2_361),
    "w53": (('RVal', [True]), 1_449, 1_456),
    "w54": (('RVal', [False]), 1_449, 1_456),
    "w55": (('RVal', [True]), 1_451, 1_458),
    "w56": (('RVal', [True]), 1_527, 1_534),
    "w57": (('RVal', [False]), 1_527, 1_534),
    "w58": (('RVal', [True]), 1_531, 1_538),
    "w59": (('RVal', [False]), 1_531, 1_538),
    "w60": (('RVal', [3]), 73_061, 69_760),
    "w61": (('RVal', [0]), 21_393, 21_034),
    "w62": (('RVal', [('Sym', 'dup')]), 2_281, 2_283),
    "w63": (('RVal', [3, 3]), 5_522, 5_494),
    "w64": (('RVal', [4]), 93_140, 88_007),
    "w65": (('RVal', [3]), 162_791, 148_117),
    "w66": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 156_782, 143_123),
    "w67": (('RVal', [[('Lit', 3), ('Lit', 4)]]), 158_594, 144_602),
    "w68": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 159_205, 145_213),
    "w69": (('RVal', [[]]), 161_021, 146_692),
    "w70": (('RErr', None), 1_483, 1_494),
    "w71": (('RVal', [True]), 5_342, 5_314),
    "w72": (('RVal', [False]), 5_342, 5_314),
    "w73": (('RVal', [[('Lit', 0), ('Lit', 1), ('Lit', 2)]]), 3_139, 3_135),
    "w74": (('RVal', [2]), 57_736, 55_614),
    "w75": (('RVal', [3]), 107_506, 100_516),
    "w76": (('RVal', [3]), 106_598, 99_726),
    "w77": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 3_311, 3_307),
    "w78": (('RVal', [True]), 2_281, 2_283),
    "w79": (('RVal', [1]), 3_999, 3_988),
    "w80": (('RVal', [2]), 57_585, 55_463),
}
COMPILED = {
    "w1": (('RVal', [12]), 343, 343),
    "w2": (('RVal', [6]), 343, 343),
    "w3": (('RVal', [4]), 343, 343),
    "w4": (('RVal', [-1]), 343, 343),
    "w5": (('RVal', [7]), 6_375, 6_417),
    "w6": (('RVal', [3]), 6_256, 6_298),
    "w7": (('RVal', [True]), 165, 165),
    "w8": (('RVal', [True]), 165, 165),
    "w9": (('RVal', [False]), 165, 165),
    "w10": (('RVal', [False]), 6_323, 6_365),
    "w11": (('RVal', [True]), 6_273, 6_315),
    "w12": (('RVal', [True]), 2_439, 2_453),
    "w13": (('RVal', [True]), 2_392, 2_406),
    "w14": (('RVal', [False]), 9_519, 9_589),
    "w15": (('RVal', [True]), 9_597, 9_667),
    "w16": (('RVal', [False]), 1_877, 1_891),
    "w17": (('RVal', [False]), 2_324, 2_338),
    "w18": (('RVal', [False]), 165, 165),
    "w19": (('RVal', [1]), 1_867, 1_881),
    "w20": (('RVal', [2]), 1_861, 1_875),
    "w21": (('RVal', [1, 2]), 3_620, 3_648),
    "w22": (('RVal', [4, 2]), 4_071, 4_099),
    "w23": (('RVal', [120]), 92_920, 92_021),
    "w24": (('RVal', [True]), 165, 165),
    "w25": (('RVal', [2]), 1_901, 1_915),
    "w26": (('RErr', None), 331, 331),
    "w27": (('RVal', [-2]), 343, 343),
    "w28": (('RVal', [3]), 461, 461),
    "w29": (('RVal', [3]), 3_233, 3_247),
    "w30": (('RVal', [-1]), 2_896, 2_910),
    "w31": (('RVal', [0]), 4_802, 4_813),
    "w32": (('RVal', [1]), 5_106, 5_117),
    "w33": (('RVal', [3]), 387, 387),
    "w34": (('RVal', [-3]), 387, 387),
    "w35": (('RVal', [-3]), 383, 383),
    "w36": (('RVal', [-1]), 387, 387),
    "w37": (('RVal', [1]), 383, 383),
    "w38": (('RErr', None), 363, 363),
    "w39": (('RVal', [-6]), 343, 343),
    "w40": (('RVal', [6]), 343, 343),
    "w41": (('RVal', [True]), 165, 165),
    "w42": (('RVal', [True]), 165, 165),
    "w43": (('RVal', [0]), 343, 343),
    "w44": (('RVal', [True]), 165, 165),
    "w45": (('RVal', [1]), 6_159, 6_201),
    "w46": (('RVal', [-1]), 343, 343),
    "w47": (('RVal', [('quot', ('RVal', [-1]))]), 82, 82),
    "w48": (('RVal', [10]), 75_883, 75_260),
    "w49": (('RVal', [1]), 670, 670),
    "w50": (('RVal', [('quot', ('RVal', [2, 3]))]), 791, 791),
    "w51": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 593, 593),
    "w52": (('RVal', [('quot', ('RVal', [2, 3])), 1]), 712, 712),
    "w53": (('RVal', [True]), 82, 82),
    "w54": (('RVal', [False]), 82, 82),
    "w55": (('RVal', [True]), 82, 82),
    "w56": (('RVal', [True]), 118, 118),
    "w57": (('RVal', [False]), 118, 118),
    "w58": (('RVal', [True]), 120, 120),
    "w59": (('RVal', [False]), 120, 120),
    "w60": (('RVal', [3]), 54_686, 54_352),
    "w61": (('RVal', [0]), 13_681, 13_666),
    "w62": (('RVal', [('Sym', 'dup')]), 664, 664),
    "w63": (('RVal', [3, 3]), 4_144, 4_155),
    "w64": (('RVal', [4]), 78_687, 78_194),
    "w65": (('RVal', [3]), 97_220, 96_802),
    "w66": (('RVal', [('quot', ('RVal', [1, 2]))]), 86_004, 85_586),
    "w67": (('RVal', [('quot', ('RVal', [3, 4]))]), 86_008, 85_590),
    "w68": (('RVal', [('quot', ('RVal', [1, 2]))]), 86_886, 86_468),
    "w69": (('RVal', [('quot', ('RVal', []))]), 86_890, 86_472),
    "w70": (('RErr', None), 622, 622),
    "w71": (('RVal', [True]), 1_598, 1_598),
    "w72": (('RVal', [False]), 1_534, 1_534),
    "w73": (('RVal', [('quot', ('RVal', [0, 1, 2]))]), 320, 320),
    "w74": (('RVal', [2]), 41_665, 41_475),
    "w75": (('RVal', [3]), 58_120, 57_930),
    "w76": (('RVal', [3]), 57_993, 57_803),
    "w77": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 2_575, 2_575),
    "w78": (('RVal', [True]), 644, 644),
    "w79": (('RVal', [1]), 3_120, 3_120),
    "w80": (('RVal', [2]), 49_160, 48_970),
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
    assert INTERPRETED["w62"][0] == COMPILED["w62"][0] == ("RVal", [("Sym", "dup")])
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
