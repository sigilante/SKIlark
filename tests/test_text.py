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
    "t1": (('RVal', [('Char', 65)]), 856, 874),
    "t2": (('RVal', [65]), 1_773, 1_787),
    "t3": (('RVal', [('Char', 66)]), 1_779, 1_793),
    "t4": (('RVal', [('Char', 66)]), 3_110, 3_119),
    "t5": (('RVal', [('Char', 97)]), 3_108, 3_117),
    "t6": (('RVal', [('Char', 66)]), 11_079, 11_026),
    "t7": (('RVal', [('Char', 98)]), 91_391, 89_767),
    "t8": (('RVal', [True]), 2_558, 2_567),
    "t9": (('RVal', [True]), 2_556, 2_565),
    "t10": (('RVal', [('Char', 1)]), 1_775, 1_789),
    "t11": (('RErr', None), 1_730, 1_748),
    "t12": (('RErr', None), 3_044, 3_058),
    "t13": (('RVal', [('Str', 'abc')]), 856, 874),
    "t14": (('RVal', [('Char', 97)]), 2_625, 2_634),
    "t15": (('RVal', [('Str', 'bc')]), 3_514, 3_517),
    "t16": (('RVal', [3]), 1_887, 1_901),
    "t17": (('RVal', [('Str', 'xab')]), 2_797, 2_806),
    "t18": (('RErr', None), 2_740, 2_754),
    "t19": (('RVal', [('Str', 'abcd')]), 2_769, 2_778),
    "t20": (('RErr', None), 2_812, 2_826),
    "t21": (('RVal', [('Char', 98)]), 3_356, 3_365),
    "t22": (('RVal', [('Str', 'ab')]), 297_715, 265_892),
    "t23": (('RVal', [('Str', 'bc')]), 116_056, 110_207),
    "t24": (('RVal', [True]), 2_558, 2_567),
    "t25": (('RVal', [True]), 2_556, 2_565),
    "t26": (('RVal', [True]), 4_349, 4_345),
    "t27": (('RVal', [True]), 1_645, 1_659),
    "t28": (('RVal', [True]), 1_779, 1_793),
    "t29": (('RVal', [('Str', 'bcd')]), 636_226, 519_424),
    "t30": (('RVal', [('Str', 'cd')]), 1_098_844, 883_455),
    "t31": (('RVal', [195]), 197_035, 180_427),
    "t32": (('RVal', [True]), 616_466, 525_166),
    "t33": (('RVal', [True]), 617_734, 526_006),
    "t34": (('RVal', [True]), 404_152, 347_602),
    "t35": (('RVal', [False]), 1_767, 1_781),
    "t36": (('RVal', [1]), 4_773, 4_769),
    "t37": (('RVal', [2]), 4_747, 4_743),
    "t38": (('RVal', [('Char', 97)]), 2_633, 2_642),
    "t39": (('RVal', [('Char', 97), ('Str', 'b'), [('Text', 'b'), ('Glyph', 97)]]), 2_424, 2_433),
    "t40": (('RVal', [3]), 1_887, 1_901),
    "t41": (('RVal', [('Char', 65)]), 856, 874),
    "t42": (('RVal', [('Char', 97), ('Str', 'b')]), 1_817, 1_831),
    "t43": (('RVal', [195]), 312_897, 277_973),
}
COMPILED = {
    "t1": (('RVal', [('Char', 65)]), 7, 7),
    "t2": (('RVal', [65]), 116, 116),
    "t3": (('RVal', [('Char', 66)]), 120, 120),
    "t4": (('RVal', [('Char', 66)]), 279, 279),
    "t5": (('RVal', [('Char', 97)]), 339, 339),
    "t6": (('RVal', [('Char', 66)]), 1_716, 1_730),
    "t7": (('RVal', [('Char', 98)]), 19_482, 19_608),
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
    "t21": (('RVal', [('Char', 98)]), 31_092, 31_013),
    "t22": (('RVal', [('Str', 'ab')]), 115_242, 114_183),
    "t23": (('RVal', [('Str', 'bc')]), 30_849, 30_770),
    "t24": (('RVal', [True]), 165, 165),
    "t25": (('RVal', [True]), 165, 165),
    "t26": (('RVal', [True]), 445, 445),
    "t27": (('RVal', [True]), 82, 82),
    "t28": (('RVal', [True]), 128, 128),
    "t29": (('RVal', [('Str', 'bcd')]), 314_435, 308_183),
    "t30": (('RVal', [('Str', 'cd')]), 456_176, 445_518),
    "t31": (('RVal', [195]), 60_661, 60_069),
    "t32": (('RVal', [True]), 290_188, 283_837),
    "t33": (('RVal', [True]), 290_315, 283_964),
    "t34": (('RVal', [True]), 179_558, 176_192),
    "t35": (('RVal', [False]), 123, 123),
    "t36": (('RVal', [1]), 584, 598),
    "t37": (('RVal', [2]), 558, 572),
    "t38": (('RVal', [('Char', 97)]), 280, 280),
    "t39": (('RVal', [('Char', 97), ('Str', 'b'), ('quot', ('RVal', [('Str', 'b'), ('Char', 97)]))]), 103, 103),
    "t40": (('RVal', [3]), 19_095, 18_761),
    "t41": (('RVal', [('Char', 65)]), 7, 7),
    "t42": (('RVal', [('Char', 97), ('Str', 'b')]), 158, 158),
    "t43": (('RVal', [195]), 125_564, 124_085),
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
