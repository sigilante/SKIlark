"""Joy's stage 6, step 2: ``typeof`` and the type tests (PLAN.md §3,
stage 6).  The kernel's ``typeof`` numbers a value's type as the
reference's globals.h does, the type tests and ``sametype`` derive from
it, and the words that took a value of any type now check theirs as the
reference does; in both forms.  Each program is compiled alone.  Every
count was measured on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted, joy

PROGRAMS = {
    "y1": '5 typeof',
    "y2": '[dup] first typeof',
    "y3": '[size] first typeof',
    "y4": '[nip] first typeof',
    "y5": 'true typeof',
    "y6": "'a typeof",
    "y7": '"ab" typeof',
    "y8": '[1] typeof',
    "y9": '[dup] first [dup] first sametype',
    "y10": '[dup] first [swap] first sametype',
    "y11": '1 2 sametype',
    "y12": '1 true sametype',
    "y13": '[nip] first [k] first sametype',
    "y14": 'true succ',
    "y15": "'a succ",
    "y16": 'true pred',
    "y17": 'true false max',
    "y18": '3 true max',
    "y19": "'a 'b max",
    "y20": 'true 5 and',
    "y21": 'true 1 xor',
    "y22": '2 3 xor',
    "y23": '[1 2] true take',
    "y24": '[1 2] false drop',
    "y25": '"abc" true take',
    "y26": "'\\002 [0] [pop] primrec",
    "y27": '"ab" [ord] map',
    "y28": '"ab" [succ] map',
    "y29": '[] 5 map',
    "y30": '0 5 times',
    "y31": '1 [pop true] [5] 7 tailrec',
    "y32": '[1] [pop false] 5 while',
    "y33": '3 integer',
    "y34": '3 logical',
    "y35": 'true logical',
    "y36": "'a char",
    "y37": '"a" string',
    "y38": '[] list',
    "y39": '[] leaf',
    "y40": '3 leaf',
    "y41": '[dup] first user',
    "y42": '[nip] first user',
    "y43": '3 float',
    "y44": '3 file',
    "y45": '[1 2 3] [2 <] filter',
    "y46": '[1 2] 3 drop',
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "y1": (('RVal', [6]), 1_515, 1_522),
    "y2": (('RVal', [3]), 3_168, 3_164),
    "y3": (('RVal', [3]), 3_168, 3_164),
    "y4": (('RVal', [2]), 3_168, 3_164),
    "y5": (('RVal', [4]), 1_515, 1_522),
    "y6": (('RVal', [5]), 1_515, 1_522),
    "y7": (('RVal', [8]), 1_515, 1_522),
    "y8": (('RVal', [9]), 1_515, 1_522),
    "y9": (('RVal', [True]), 24_613, 24_226),
    "y10": (('RVal', [False]), 24_605, 24_218),
    "y11": (('RVal', [True]), 11_394, 11_292),
    "y12": (('RVal', [False]), 11_386, 11_284),
    "y13": (('RVal', [True]), 15_225, 15_053),
    "y14": (('RVal', [2]), 13_190, 13_072),
    "y15": (('RVal', [('Char', 98)]), 9_348, 9_288),
    "y16": (('RVal', [0]), 13_188, 13_070),
    "y17": (('RVal', [1]), 53_571, 51_763),
    "y18": (('RErr', None), 18_461, 18_227),
    "y19": (('RVal', [('Char', 98)]), 60_487, 58_856),
    "y20": (('RErr', None), 18_449, 18_215),
    "y21": (('RErr', None), 18_449, 18_215),
    "y22": (('RVal', [True]), 34_399, 33_639),
    "y23": (('RVal', [[('Lit', 1)]]), 277_396, 243_774),
    "y24": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 64_886, 62_349),
    "y25": (('RVal', [('Str', 'a')]), 352_465, 301_801),
    "y26": (('RErr', None), 34_300, 33_617),
    "y27": (('RVal', [('Str', 'ab')]), 394_497, 334_526),
    "y28": (('RVal', [('Str', 'bc')]), 419_870, 353_502),
    "y29": (('RErr', None), 10_891, 10_818),
    "y30": (('RErr', None), 10_891, 10_818),
    "y31": (('RErr', None), 12_458, 12_356),
    "y32": (('RErr', None), 11_674, 11_587),
    "y33": (('RVal', [True]), 3_102, 3_098),
    "y34": (('RVal', [False]), 3_102, 3_098),
    "y35": (('RVal', [True]), 3_102, 3_098),
    "y36": (('RVal', [True]), 3_102, 3_098),
    "y37": (('RVal', [True]), 3_102, 3_098),
    "y38": (('RVal', [True]), 3_102, 3_098),
    "y39": (('RVal', [False]), 7_638, 7_600),
    "y40": (('RVal', [True]), 7_462, 7_424),
    "y41": (('RVal', [False]), 4_759, 4_740),
    "y42": (('RVal', [True]), 4_759, 4_740),
    "y43": (('RVal', [False]), 2_317, 2_319),
    "y44": (('RVal', [False]), 2_317, 2_319),
    "y45": (('RVal', [[('Lit', 1)]]), 457_238, 376_694),
    "y46": (('RVal', [[]]), 148_603, 137_759),
}
COMPILED = {
    "y1": (('RVal', [6]), 82, 82),
    "y2": (('RVal', [3]), 341, 341),
    "y3": (('RVal', [3]), 405, 405),
    "y4": (('RVal', [2]), 345, 345),
    "y5": (('RVal', [4]), 82, 82),
    "y6": (('RVal', [5]), 82, 82),
    "y7": (('RVal', [8]), 82, 82),
    "y8": (('RVal', [9]), 82, 82),
    "y9": (('RVal', [True]), 4_201, 4_209),
    "y10": (('RVal', [False]), 4_227, 4_235),
    "y11": (('RVal', [True]), 1_612, 1_626),
    "y12": (('RVal', [False]), 1_604, 1_618),
    "y13": (('RVal', [True]), 2_496, 2_510),
    "y14": (('RVal', [2]), 1_952, 1_963),
    "y15": (('RVal', [('Char', 98)]), 1_716, 1_730),
    "y16": (('RVal', [0]), 2_052, 2_063),
    "y17": (('RVal', [1]), 9_014, 9_137),
    "y18": (('RErr', None), 2_781, 2_823),
    "y19": (('RVal', [('Char', 98)]), 19_482, 19_608),
    "y20": (('RErr', None), 2_697, 2_739),
    "y21": (('RErr', None), 2_661, 2_703),
    "y22": (('RVal', [True]), 6_111, 6_195),
    "y23": (('RVal', [('quot', ('RVal', [1]))]), 96_352, 95_614),
    "y24": (('RVal', [('quot', ('RVal', [1, 2]))]), 17_098, 17_136),
    "y25": (('RVal', [('Str', 'a')]), 124_570, 123_417),
    "y26": (('RErr', None), 12_156, 12_188),
    "y27": (('RVal', [('Str', 'ab')]), 210_550, 207_326),
    "y28": (('RVal', [('Str', 'bc')]), 223_689, 220_382),
    "y29": (('RErr', None), 2_340, 2_354),
    "y30": (('RErr', None), 1_920, 1_934),
    "y31": (('RErr', None), 1_855, 1_869),
    "y32": (('RErr', None), 1_792, 1_806),
    "y33": (('RVal', [True]), 240, 240),
    "y34": (('RVal', [False]), 240, 240),
    "y35": (('RVal', [True]), 240, 240),
    "y36": (('RVal', [True]), 240, 240),
    "y37": (('RVal', [True]), 240, 240),
    "y38": (('RVal', [True]), 240, 240),
    "y39": (('RVal', [False]), 1_458, 1_472),
    "y40": (('RVal', [True]), 1_272, 1_286),
    "y41": (('RVal', [False]), 499, 499),
    "y42": (('RVal', [True]), 503, 503),
    "y43": (('RVal', [False]), 128, 128),
    "y44": (('RVal', [False]), 128, 128),
    "y45": (('RVal', [('quot', ('RVal', [1]))]), 256_601, 250_397),
    "y46": (('RVal', [('quot', ('RVal', []))]), 43_631, 43_380),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_types(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_types(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_typeof_numbers_the_types_as_the_reference_does():
    """globals.h: a user-defined symbol 2, a builtin 3, a truth value 4, a
    character 5, an integer 6, a string 8, a list 9."""
    want = {"y1": 6, "y2": 3, "y3": 3, "y4": 2, "y5": 4, "y6": 5, "y7": 8, "y8": 9}
    for name, n in want.items():
        assert INTERPRETED[name][0] == COMPILED[name][0] == ("RVal", [n]), PROGRAMS[name]


@pytest.mark.parametrize("make", [interpreted, compiled])
def test_a_programs_own_definition_is_user_defined(make):
    """A definition the program brings is a user symbol, and so is one of
    Joy's names given another body; Joy's own body keeps its builtin."""
    defs = dict(joy.DEFINITIONS, sq="dup +", size="pop 7")
    r = make({"a": "[sq] first typeof", "b": "[size] first user",
              "c": "[over] first user"}, defs)
    assert [r.run(f"u{n}")[0] for n in "abc"] == \
        [("RVal", [2]), ("RVal", [True]), ("RVal", [False])]


def test_a_program_without_typeof_keeps_its_compiled_kernel():
    """The compiled form has typeof only where a program asks a type, so
    every other program, zk's verifiers among them, compiles as before."""
    assert "kindOf" not in joy.compiled({"p": "[1 2] first 3 <"})
    assert "kindOf" in joy.compiled({"p": "3 integer"})


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "X leaf == X list not":              ("[1] leaf 3 leaf", "[1] list not 3 list not"),
    "X Y sametype == Y X sametype":      ("1 'a sametype", "'a 1 sametype"),
    "b succ pred == b ord":              ("true succ pred", "true ord"),
    "c succ pred == c":                  ("'a succ pred", "'a"),
    "A b take A b drop concat == A":     ("[1 2 3] true take [1 2 3] true drop concat", "[1 2 3]"),
    "x y max == y x max":                ("'a 'b max", "'b 'a max"),
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
