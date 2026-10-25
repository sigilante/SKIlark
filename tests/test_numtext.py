"""Joy's stage 11: numbers to and from text (PLAN.md §3, stage 11):
``strtol format``, ext's ``Strtol Format``, kernel words in both forms on
programs/numtext.ascii.ski, which comes only with a program that uses one.
``strtol`` reads as glibc's strtoll does, ``format`` writes printf's
%*.*lld under its conversion.  A format's result is compared with the
reference's string, not read back: an interpreted string is read a
character at a time, each probe a run.  Every count was measured on
skijack 0.2.3.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "x1": '"123" 10 strtol 123 =',
    "x2": '"  -42xyz" 10 strtol -42 =',
    "x3": '"0x1f" 0 strtol 31 =',
    "x4": '"017" 0 strtol',
    "x5": '"ff" 16 strtol 255 =',
    "x6": '"0xff" 16 strtol 255 =',
    "x7": '"z" 36 strtol 35 =',
    "x8": '"12" 1 strtol',
    "x9": '"abc" 10 strtol',
    "x10": '"+7" 0 strtol',
    "x11": '"0x" 0 strtol',
    "x12": '"" 10 strtol',
    "x13": '"10" -2 strtol',
    "x14": '"10" 37 strtol',
    "x15": '"101" 2 strtol',
    "x16": '5 "1" strtol',
    "x17": '"1" 2 3 strtol',
    "x18": '10 strtol',
    "x19": '42 \'d 5 2 format "   42" =',
    "x20": '-42 \'d 6 4 format " -0042" =',
    "x21": '255 \'x 0 0 format "ff" =',
    "x22": '255 \'X -6 1 format "FF    " =',
    "x23": '8 \'o 3 -1 format " 10" =',
    "x24": '0 \'d 0 0 format "" =',
    "x25": '0 \'d 3 1 format "  0" =',
    "x26": 'true \'d 2 1 format " 1" =',
    "x27": '\'A \'d 1 1 format "65" =',
    "x28": '7 \'i -3 0 format "7  " =',
    "x29": '12 \'x 4 3 format " 00c" =',
    "x30": "5 'q 1 1 format",
    "x31": "5 'd true 1 format",
    "x32": '"a" \'d 1 1 format',
    "x33": "'d 1 1 format",
    "x34": "5 'd 1 'a format",
}

INTERPRETED = {
    "x1": (('RVal', [True]), 4_801, 4_797),
    "x2": (('RVal', [True]), 4_801, 4_797),
    "x3": (('RVal', [True]), 4_801, 4_797),
    "x4": (('RVal', [15]), 3_084, 3_093),
    "x5": (('RVal', [True]), 4_801, 4_797),
    "x6": (('RVal', [True]), 4_801, 4_797),
    "x7": (('RVal', [True]), 4_801, 4_797),
    "x8": (('RVal', [0]), 3_084, 3_093),
    "x9": (('RVal', [0]), 3_084, 3_093),
    "x10": (('RVal', [7]), 3_084, 3_093),
    "x11": (('RVal', [0]), 3_084, 3_093),
    "x12": (('RVal', [0]), 3_084, 3_093),
    "x13": (('RVal', [0]), 3_084, 3_093),
    "x14": (('RVal', [0]), 3_084, 3_093),
    "x15": (('RVal', [5]), 3_084, 3_093),
    "x16": (('RErr', None), 2_880, 2_894),
    "x17": (('RErr', None), 3_858, 3_867),
    "x18": (('RErr', None), 2_082, 2_100),
    "x19": (('RVal', [True]), 25_456, 25_435),
    "x20": (('RVal', [True]), 25_456, 25_435),
    "x21": (('RVal', [True]), 88_478, 88_457),
    "x22": (('RVal', [True]), 84_584, 84_563),
    "x23": (('RVal', [True]), 65_520, 65_499),
    "x24": (('RVal', [True]), 25_456, 25_435),
    "x25": (('RVal', [True]), 25_456, 25_435),
    "x26": (('RVal', [True]), 25_452, 25_431),
    "x27": (('RVal', [True]), 25_448, 25_427),
    "x28": (('RVal', [True]), 44_773, 44_752),
    "x29": (('RVal', [True]), 88_478, 88_457),
    "x30": (('RErr', None), 99_966, 99_969),
    "x31": (('RErr', None), 4_811, 4_814),
    "x32": (('RErr', None), 23_627, 23_630),
    "x33": (('RErr', None), 22_281, 22_290),
    "x34": (('RErr', None), 4_552, 4_555),
}

COMPILED = {
    "x1": (('RVal', [True]), 418, 418),
    "x2": (('RVal', [True]), 418, 418),
    "x3": (('RVal', [True]), 418, 418),
    "x4": (('RVal', [15]), 235, 235),
    "x5": (('RVal', [True]), 429, 429),
    "x6": (('RVal', [True]), 429, 429),
    "x7": (('RVal', [True]), 418, 418),
    "x8": (('RVal', [0]), 235, 235),
    "x9": (('RVal', [0]), 235, 235),
    "x10": (('RVal', [7]), 235, 235),
    "x11": (('RVal', [0]), 235, 235),
    "x12": (('RVal', [0]), 235, 235),
    "x13": (('RVal', [0]), 235, 235),
    "x14": (('RVal', [0]), 235, 235),
    "x15": (('RVal', [5]), 235, 235),
    "x16": (('RErr', None), 159, 159),
    "x17": (('RErr', None), 281, 281),
    "x18": (('RErr', None), 127, 127),
    "x19": (('RVal', [True]), 18_925, 18_925),
    "x20": (('RVal', [True]), 18_925, 18_925),
    "x21": (('RVal', [True]), 81_952, 81_952),
    "x22": (('RVal', [True]), 78_058, 78_058),
    "x23": (('RVal', [True]), 58_989, 58_989),
    "x24": (('RVal', [True]), 18_925, 18_925),
    "x25": (('RVal', [True]), 18_925, 18_925),
    "x26": (('RVal', [True]), 18_921, 18_921),
    "x27": (('RVal', [True]), 18_919, 18_919),
    "x28": (('RVal', [True]), 38_242, 38_242),
    "x29": (('RVal', [True]), 81_947, 81_947),
    "x30": (('RErr', None), 95_382, 95_382),
    "x31": (('RErr', None), 372, 372),
    "x32": (('RErr', None), 18_655, 18_655),
    "x33": (('RErr', None), 18_475, 18_475),
    "x34": (('RErr', None), 259, 259),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_numtext(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_numtext(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_a_program_that_uses_neither_carries_neither():
    """numtext's words come only with a program that uses one."""
    plain, used = (interpreted({"p": p}).e.sizes for p in ("1", '"1" 10 strtol'))
    assert "formatF" not in plain and "formatF" in used


# ---------------------------------------------------- the laws, both forms

#: each side a truth value or a small number: a numeral is read a
#: successor at a time, each probe a run
LAWS = {
    "N 'd 0 1 format 10 strtol == N":        ("255 'd 0 1 format 10 strtol 255 =", "true"),
    "N 'x 0 1 format 16 strtol == N":        ("255 'x 0 1 format 16 strtol 255 =", "true"),
    "S 0 strtol == S 10 strtol (decimal)":   ('"77" 0 strtol "77" 10 strtol =', "true"),
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
