"""Joy's stage 10: symbols and their names (PLAN.md §3, stage 10):
``name body intern``, ext's ``Name Body Intern``.  ``name`` gives a
symbol's nickname (``+`` is ``plus``) or a literal's type's name, ``body``
a user definition's quotation; ``intern`` reads a name and finds its
word, in the interpreted form alone (its table holds every Joy word, and
the compiled form's symbols are the program's own).  Every count was
measured on skijack 0.2.3.
"""

import pytest

import skilark
from skilark import compiled, interpreted

PROGRAMS = {
    "s1": '[dup] first name "dup" =',
    "s2": '[+] first name "plus" =',
    "s3": '[>=] first name "geql" =',
    "s4": '[size] first name "size" =',
    "s5": '[nip] first name "nip" =',
    "s6": '5 name "integer type" =',
    "s7": '[] name "list type" =',
    "s8": '"a" name "string type" =',
    "s9": 'true name "truth value type" =',
    "s10": '\'a name "character type" =',
    "s11": '{1} name "set type" =',
    "s12": 'name',
    "s13": '[nip] first body',
    "s14": '[dup] first body',
    "s15": '[map] first body',
    "s16": '5 body',
    "s17": '1 2 [nip] first body i',
    "s18": '[tuck] first body size',
    "s19": '[compare] first name "compare" =',
    "s20": '[-] first name size',
    "s21": '[>] first',
    "s22": '[[>] [!=]] [dup] infra',
}

INTERPRETED = {
    "s1": (('RVal', [True]), 5_493, 5_481),
    "s2": (('RVal', [True]), 5_493, 5_481),
    "s3": (('RVal', [True]), 5_493, 5_481),
    "s4": (('RVal', [True]), 5_493, 5_481),
    "s5": (('RVal', [True]), 5_493, 5_481),
    "s6": (('RVal', [True]), 3_703, 3_706),
    "s7": (('RVal', [True]), 3_703, 3_706),
    "s8": (('RVal', [True]), 3_703, 3_706),
    "s9": (('RVal', [True]), 3_703, 3_706),
    "s10": (('RVal', [True]), 3_703, 3_706),
    "s11": (('RVal', [True]), 3_703, 3_706),
    "s12": (('RErr', None), 1_065, 1_086),
    "s13": (('RVal', [[('Quote', ['Pop']), 'Dip']]), 4_279, 4_282),
    "s14": (('RErr', None), 4_135, 4_144),
    "s15": (('RErr', None), 4_214, 4_223),
    "s16": (('RErr', None), 2_023, 2_041),
    "s17": (('RVal', [2]), 10_674, 10_608),
    "s18": (('RVal', [3]), 5_542, 5_538),
    "s19": (('RVal', [True]), 5_493, 5_481),
    "s20": (('RVal', [5]), 5_040, 5_036),
    "s21": (('RVal', [('Sym', '>')]), 2_633, 2_642),
    "s22": (('RVal', [[('Quote', [('Def', '>')]), ('Quote', [('Def', '>')]), ('Quote', [('Def', '!=')])]]), 28_835, 28_334),
}

COMPILED = {
    "s1": (('RVal', [True]), 517, 517),
    "s2": (('RVal', [True]), 517, 517),
    "s3": (('RVal', [True]), 517, 517),
    "s4": (('RVal', [True]), 581, 581),
    "s5": (('RVal', [True]), 521, 521),
    "s6": (('RVal', [True]), 240, 240),
    "s7": (('RVal', [True]), 240, 240),
    "s8": (('RVal', [True]), 240, 240),
    "s9": (('RVal', [True]), 240, 240),
    "s10": (('RVal', [True]), 240, 240),
    "s11": (('RVal', [True]), 240, 240),
    "s12": (('RErr', None), 6, 6),
    "s13": (('RVal', [('quot', ('RErr', None))]), 398, 398),
    "s14": (('RErr', None), 373, 373),
    "s15": (('RErr', None), 624, 624),
    "s16": (('RErr', None), 109, 109),
    "s17": (('RVal', [2]), 1_113, 1_124),
    "s18": (('RVal', [3]), 20_375, 20_041),
    "s19": (('RVal', [True]), 517, 517),
    "s20": (('RVal', [5]), 30_164, 29_457),
    "s21": (('RVal', [('Sym', '>')]), 278, 278),
    "s22": (('RVal', [('quot', ('RVal', [('quot', ('RErr', None)), ('quot', ('RErr', None)), ('quot', ('RErr', None))]))]), 7_288, 7_283),
}

#: intern's programs, interpreted alone
INTERN = {
    "i1": '"dup" intern',
    "i2": '"zork" intern typeof',
    "i3": '"nip" intern body',
    "i4": '1 2 "nip" intern unit i',
    "i5": '"3x" intern',
    "i6": '"a b" intern',
    "i7": '"over" intern typeof',
    "i8": '"+" intern',
    "i9": '"Zork" intern name size',
    "i10": '5 intern',
    "i11": '[size] first name intern',
    "i12": '"-5" intern',
}

INTERN_INTERPRETED = {
    "i1": (('RVal', [('Sym', 'dup')]), 482_205, 482_219),
    "i2": (('RVal', [2]), 697_823, 697_832),
    "i3": (('RVal', [[('Quote', ['Pop']), 'Dip']]), 2_311_384, 2_311_393),
    "i4": (('RVal', [2]), 2_318_102, 2_318_036),
    "i5": (('RErr', None), 26_847, 26_865),
    "i6": (('RErr', None), 40_907, 40_925),
    "i7": (('RVal', [3]), 697_157, 697_166),
    "i8": (('RVal', [('Sym', '+')]), 24_889, 24_903),
    "i9": (('RVal', [4]), 699_445, 699_448),
    "i10": (('RErr', None), 2_009, 2_027),
    "i11": (('RVal', [('Sym', 'size')]), 2_056_992, 2_056_988),
    "i12": (('RErr', None), 42_468, 42_486),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_symbols(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_symbols(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.fixture(scope="module")
def interp_intern():
    return interpreted(INTERN)


@pytest.fixture
def long_reads(monkeypatch):
    """A reader's probe runs the program again from its root, and an intern
    program, its table a kernel of 1.6 million atoms, takes up to 2.3
    million contractions: past the probe's cap, so this module's raises it."""
    monkeypatch.setattr(skilark, "STEPS", 50_000_000)


@pytest.mark.parametrize("name", sorted(INTERN))
def test_interpreted_intern(interp_intern, long_reads, name):
    """One test a program, so that shards share the runs: the table's
    kernel compiles in seconds, and the runs take the reference minutes."""
    outcome, unfuelled, fuelled = INTERN_INTERPRETED[name]
    assert interp_intern.run("u" + name) == (outcome, unfuelled), INTERN[name]
    assert interp_intern.run("r" + name) == (outcome, fuelled), INTERN[name]


def test_the_compiled_form_refuses_intern():
    with pytest.raises(ValueError, match="interpreted form's alone"):
        compiled({"p": '"dup" intern'})


def test_a_program_that_neither_names_nor_interns_carries_neither():
    """name's and intern's words come only with a program that uses one,
    so the kernel every other program runs on stays as it was."""
    plain, named = (interpreted({"p": p}).e.sizes for p in ("1", "5 name"))
    assert "nameText" not in plain and "internW" not in plain
    assert named["step"] > plain["step"] and "iw0" not in named


# ---------------------------------------------------- the laws

#: each side a truth value, so that no law reads a string back: an
#: interpreted string is read a character at a time, each probe a run
LAWS = {
    "[nip] first body == [[pop] dip]":        ("[nip] first body [[pop] dip] equal", "true"),
    "[dup] first name == \"dup\"":            ('[dup] first name "dup" =', "true"),
    "5 name == \"integer type\"":             ('5 name "integer type" =', "true"),
}
INTERN_LAWS = {
    "\"dup\" intern == [dup] first":          ('"dup" intern [dup] first =', "true"),
    "[P] first name intern == [P] first":     ("[size] first name intern [size] first =", "true"),
}


def _law_programs(laws):
    return {f"l{i}{side}": text for i, (l, r) in enumerate(laws.values())
            for side, text in (("L", l), ("R", r))}


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_compiled(i):
    progs = _law_programs(LAWS)
    left, right = (compiled({"p": progs[f"l{i}{side}"]}).run("up")[0] for side in ("L", "R"))
    assert left == right and left[0] == "RVal", list(LAWS)[i]


ALL_LAWS = {**LAWS, **INTERN_LAWS}


@pytest.fixture(scope="module")
def interp_laws():
    return interpreted(_law_programs(ALL_LAWS))


@pytest.mark.parametrize("i", range(len(ALL_LAWS)))
def test_each_law_holds_interpreted(interp_laws, long_reads, i):
    left, right = interp_laws.run(f"ul{i}L")[0], interp_laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(ALL_LAWS)[i]
