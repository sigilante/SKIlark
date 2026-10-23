"""Joy's stage 5, characters and strings (PLAN.md §3, "Toward Joy in
full"): a character is its code, a string the codes of its characters, and
the list words take strings as the reference's do; in both forms.  Each
program is compiled alone.  Every count was measured on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "t1": "'A",
    "t2": "'A ord",
    "t3": "66 chr",
    "t4": "'A 1 +",
    "t5": "'b 1 -",
    "t6": "'A succ",
    "t7": "'a 'b max",
    "t8": "'A 65 =",
    "t9": "'a 'b <",
    "t10": "true chr",
    "t11": "[] ord",
    "t12": "'A 2 *",
    "t13": '"abc"',
    "t14": '"abc" first',
    "t15": '"abc" rest',
    "t16": '"abc" size',
    "t17": "'x \"ab\" cons",
    "t18": '1 "ab" cons',
    "t19": '"ab" "cd" concat',
    "t20": '"ab" [1] concat',
    "t21": '"abc" 1 at',
    "t22": '"abc" 2 take',
    "t23": '"abc" 1 drop',
    "t24": '"ab" "ab" =',
    "t25": '"ab" "b" <',
    "t26": '"dup" [dup] first =',
    "t27": '"" null',
    "t28": '"a" small',
    "t29": '"abc" [succ] map',
    "t30": '"abcd" [ord 98 >] filter',
    "t31": '"ab" 0 [ord +] fold',
    "t32": '"abc" 98 has',
    "t33": "'b \"abc\" in",
    "t34": "[1 2] 2 has",
    "t35": "'A not",
    "t36": '"x" [1] [2] branch',
    "t37": '"" [1] [2] branch',
    "t38": "['a \"b\"] first",
    "t39": "'a \"b\" stack",
    "t40": '"a\\nb" size',
    "t41": "'\\065",
    "t42": '"ab" uncons',
    "t43": '"ab" [0] [[ord] dip +] primrec',
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "t1": (('RVal', [('Char', 65)]), 766, 777),
    "t2": (('RVal', [65]), 1_578, 1_585),
    "t3": (('RVal', [('Char', 66)]), 1_584, 1_591),
    "t4": (('RVal', [('Char', 66)]), 2_764, 2_766),
    "t5": (('RVal', [('Char', 97)]), 2_762, 2_764),
    "t6": (('RVal', [('Char', 66)]), 2_764, 2_766),
    "t7": (('RVal', [('Char', 98)]), 33_061, 32_615),
    "t8": (('RVal', [True]), 2_294, 2_296),
    "t9": (('RVal', [True]), 2_292, 2_294),
    "t10": (('RVal', [('Char', 1)]), 1_580, 1_587),
    "t11": (('RErr', None), 1_535, 1_546),
    "t12": (('RErr', None), 2_698, 2_705),
    "t13": (('RVal', [('Str', 'abc')]), 766, 777),
    "t14": (('RVal', [('Char', 97)]), 2_346, 2_348),
    "t15": (('RVal', [('Str', 'bc')]), 3_151, 3_147),
    "t16": (('RVal', [3]), 76_370, 73_069),
    "t17": (('RVal', [('Str', 'xab')]), 2_482, 2_484),
    "t18": (('RErr', None), 2_425, 2_432),
    "t19": (('RVal', [('Str', 'abcd')]), 2_454, 2_456),
    "t20": (('RErr', None), 2_497, 2_504),
    "t21": (('RVal', [('Char', 98)]), 137_941, 127_390),
    "t22": (('RVal', [('Str', 'ab')]), 426_349, 350_558),
    "t23": (('RVal', [('Str', 'bc')]), 136_069, 125_807),
    "t24": (('RVal', [True]), 2_294, 2_296),
    "t25": (('RVal', [True]), 2_292, 2_294),
    "t26": (('RVal', [True]), 3_896, 3_885),
    "t27": (('RVal', [True]), 1_471, 1_478),
    "t28": (('RVal', [True]), 1_584, 1_591),
    "t29": (('RVal', [('Str', 'bcd')]), 348_490, 294_592),
    "t30": (('RVal', [('Str', 'cd')]), 680_514, 544_095),
    "t31": (('RVal', [195]), 133_738, 123_476),
    "t32": (('RVal', [True]), 412_998, 349_869),
    "t33": (('RVal', [True]), 414_108, 350_623),
    "t34": (('RVal', [True]), 274_478, 238_749),
    "t35": (('RVal', [False]), 6_578, 6_540),
    "t36": (('RVal', [1]), 4_272, 4_261),
    "t37": (('RVal', [2]), 4_246, 4_235),
    "t38": (('RVal', [('Char', 97)]), 2_354, 2_356),
    "t39": (('RVal', [('Char', 97), ('Str', 'b'), [('Text', 'b'), ('Glyph', 97)]]), 2_160, 2_162),
    "t40": (('RVal', [3]), 76_370, 73_069),
    "t41": (('RVal', [('Char', 65)]), 766, 777),
    "t42": (('RVal', [('Char', 97), ('Str', 'b')]), 1_622, 1_629),
    "t43": (('RVal', [195]), 256_406, 224_323),
}
COMPILED = {
    "t1": (('RVal', [('Char', 65)]), 7, 7),
    "t2": (('RVal', [65]), 116, 116),
    "t3": (('RVal', [('Char', 66)]), 120, 120),
    "t4": (('RVal', [('Char', 66)]), 279, 279),
    "t5": (('RVal', [('Char', 97)]), 339, 339),
    "t6": (('RVal', [('Char', 66)]), 279, 279),
    "t7": (('RVal', [('Char', 98)]), 13_082, 13_138),
    "t8": (('RVal', [True]), 165, 165),
    "t9": (('RVal', [True]), 165, 165),
    "t10": (('RVal', [('Char', 1)]), 125, 125),
    "t11": (('RErr', None), 114, 114),
    "t12": (('RErr', None), 331, 331),
    "t13": (('RVal', [('Str', 'abc')]), 7, 7),
    "t14": (('RVal', [('Char', 97)]), 235, 235),
    "t15": (('RVal', [('Str', 'bc')]), 358, 358),
    "t16": (('RVal', [3]), 19_095, 18_761),
    "t17": (('RVal', [('Str', 'xab')]), 239, 239),
    "t18": (('RErr', None), 234, 234),
    "t19": (('RVal', [('Str', 'abcd')]), 229, 229),
    "t20": (('RErr', None), 242, 242),
    "t21": (('RVal', [('Char', 98)]), 31_675, 31_485),
    "t22": (('RVal', [('Str', 'ab')]), 122_400, 121_087),
    "t23": (('RVal', [('Str', 'bc')]), 31_432, 31_242),
    "t24": (('RVal', [True]), 165, 165),
    "t25": (('RVal', [True]), 165, 165),
    "t26": (('RVal', [True]), 445, 445),
    "t27": (('RVal', [True]), 82, 82),
    "t28": (('RVal', [True]), 128, 128),
    "t29": (('RVal', [('Str', 'bcd')]), 172_006, 166_242),
    "t30": (('RVal', [('Str', 'cd')]), 408_898, 397_997),
    "t31": (('RVal', [195]), 44_162, 43_524),
    "t32": (('RVal', [True]), 248_906, 242_521),
    "t33": (('RVal', [True]), 249_012, 242_627),
    "t34": (('RVal', [True]), 153_195, 149_795),
    "t35": (('RVal', [False]), 862, 876),
    "t36": (('RVal', [1]), 584, 598),
    "t37": (('RVal', [2]), 558, 572),
    "t38": (('RVal', [('Char', 97)]), 280, 280),
    "t39": (('RVal', [('Char', 97), ('Str', 'b'), ('quot', ('RVal', [('Str', 'b'), ('Char', 97)]))]), 103, 103),
    "t40": (('RVal', [3]), 19_095, 18_761),
    "t41": (('RVal', [('Char', 65)]), 7, 7),
    "t42": (('RVal', [('Char', 97), ('Str', 'b')]), 158, 158),
    "t43": (('RVal', [195]), 99_747, 97_911),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_text(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_text(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_a_character_is_a_number_to_arithmetic_and_comparison():
    """``+`` and ``-`` take a character below an integer and give a
    character; ``=`` compares a character with an integer by code."""
    assert INTERPRETED["t4"][0] == ("RVal", [("Char", 66)])
    assert INTERPRETED["t8"][0] == ("RVal", [True])
    assert INTERPRETED["t12"][0] == ("RErr", None)


def test_a_string_compares_with_a_symbol_by_name():
    """The reference's comparison reads a string and a symbol by their
    characters: ``"dup" [dup] first =`` is true."""
    assert INTERPRETED["t26"][0] == COMPILED["t26"][0] == ("RVal", [True])


def test_a_program_without_characters_keeps_its_compiled_kernel():
    """The compiled form has characters and strings only where a program
    has one, so every other program, zk's verifiers among them, compiles as
    before."""
    from skilark import joy
    assert "Str text" not in joy.compiled({"p": "[1 2] first 3 <"})
    assert "Str text" in joy.compiled({"p": "'a"})
    assert "Str text" in joy.compiled({"p": "65 chr"})


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "c ord chr == c":                    ("'q ord chr", "'q"),
    "n chr ord == n":                    ("70 chr ord", "70"),
    "c 1 + 1 - == c":                    ("'m 1 + 1 -", "'m"),
    "S T concat size == S size T size +": ('"ab" "c" concat size', '"ab" size "c" size +'),
    "c S cons uncons == c S":            ("'z \"ab\" cons uncons", "'z \"ab\""),
    "S n take S n drop concat == S":     ('"abc" 1 take "abc" 1 drop concat', '"abc"'),
    "S [P] map size == S size":          ('"abc" [succ] map size', '"abc" size'),
}
LAW_PROGRAMS = {f"l{i}{side}": text
                for i, (l, r) in enumerate(LAWS.values())
                for side, text in (("L", l), ("R", r))}


@pytest.fixture(scope="module")
def interp_laws():
    return interpreted(LAW_PROGRAMS)


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_interpreted(interp_laws, i):
    left, right = interp_laws.run(f"ul{i}L")[0], interp_laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(LAWS)[i]


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_compiled(i):
    left, right = (compiled({"p": LAW_PROGRAMS[f"l{i}{side}"]}).run("up")[0]
                   for side in ("L", "R"))
    assert left == right and left[0] == "RVal", list(LAWS)[i]
