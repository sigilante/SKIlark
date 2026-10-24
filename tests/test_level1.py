"""Phase 2, level 1: the same program under SKIjack's blocking interpreter
``wfN``, with a definition in the namespace read by scry.  These runs take
minutes on the reference reducer, so they are ``slow`` (``--runslow``);
their numbers are recorded in PLAN.md.  The compiled ones were measured
on skijack 0.2.0 and hold on 0.2.1; the interpreted ones are the kernel's
with Joy's stages 1 to 5, measured on 0.2.1, where Avon runs them in
under a minute (``SKIJACK_REDUCER=avon``).  The fast tests below check the generated source and the reader.
"""

import pytest

import skijack
from skilark import Run, joy, level1
from skilark.joy import DEFINITIONS

DEFS = dict(DEFINITIONS, sq="dup +")

#: host contractions, measured once (PLAN.md section 1c)
LEVEL1_IQ, LEVEL1_IP = (42_440_422, 42_493_116), (43_700_623, 43_754_325)
LEVEL1_CQ, LEVEL1_CP = (2_328_665, 2_342_964), (2_337_648, 2_351_954)
READER_YES, READER_NO, READER_TQ, READER_TE, READER_TERR = 328_277, 336_136, 144_349, 33_204, 14_794
READER_TL, READER_NEG, READER_SYM = 141_273, 166_307, 138_542
READER_TC, READER_TS, READER_TZ = 136_152, 134_099, 132_379

#: (form, program, fuel) -> (outcome, host contractions)
MEASURED = {
    ("interpreted", "1 2 + dup +", 7000): LEVEL1_IQ,
    ("interpreted", "1 2 + sq", 7000):    LEVEL1_IP,
    ("compiled", "1 2 + dup +", 1500):    LEVEL1_CQ,
    ("compiled", "1 2 + sq", 1500):       LEVEL1_CP,
}


# ------------------------------------------------------------ the source

def test_a_namespace_name_becomes_a_fact_and_a_scry():
    src = joy.level1({"p": "1 2 + sq"}, ["sq"], 100, DEFS, value=6)
    assert "seg === Sq" in src
    assert "dict := ns{/sq => <Then Dup (Then Add (Done))>}" in src
    assert "rp := wfN dict |- <topIs (Suc (Suc (Suc (Suc (Suc (Suc Zero)))))) (execU (Then (Lit (Num (Pos (Suc Zero)))) (Then (Lit (Num (Pos (Suc (Suc Zero))))) (Then Add (cat ?^/sq (Done))))) Empty)>@100" in src
    assert "np := wfN dict |- <topIs (Suc (Suc (Suc (Suc (Suc (Suc (Suc Zero))))))) (execU" in src


def test_the_compiled_form_puts_the_definition_in_as_a_body():
    src = joy.level1({"p": "1 2 + sq"}, ["sq"], 100, DEFS, "compiled")
    assert "dict := ns{/sq => <seq wDup (wAdd)>}" in src
    assert "<topIs Zero (seq (wLit (Suc Zero)) (seq (wLit (Suc (Suc Zero))) (seq wAdd (?^/sq))) Empty)>@100" in src


def test_a_namespace_name_must_be_alphabetic():
    with pytest.raises(ValueError, match="alphabetic"):
        joy.level1({"p": "1 +"}, ["+"], 100, dict(DEFS, **{"+": "dup"}))


@pytest.mark.parametrize("form", ["interpreted", "compiled"])
def test_both_forms_compile_and_type_check_under_wfn(form):
    r = level1({"p": "1 2 + sq", "q": "3 sumto"}, ["sq"], 100, DEFS, form)
    assert set(r.e.level1) == {"rp", "np", "rq", "nq"}


# ------------------------------------------------------------ the reader

READER = joy.interpreted({}) + joy.LEVEL1_KERNEL.format(SEGS="Sq") + joy.LEVEL1_READER + """
dict := ns{}

yes  := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Num (Pos (Suc (Suc Zero)))) Empty))>@400
no   := wfN dict |- <topIs (Suc (Suc (Suc Zero))) (RVal (Push (Num (Pos (Suc (Suc Zero)))) Empty))>@400
neg  := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Num (Neg (Suc Zero))) Empty))>@400
sym  := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Sym Dup) Empty))>@400
tq   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Quot Done) Empty))>@400
te   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal Empty)>@400
terr := wfN dict |- <topIs (Suc (Suc Zero)) RErr>@400
tl   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Logical True) Empty))>@400
tc   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Char (Pos (Suc (Suc Zero)))) Empty))>@400
ts   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Str TNil) Empty))>@400
tz   := wfN dict |- <topIs (Suc (Suc Zero)) (RVal (Push (Set SNil) Empty))>@400
"""


def test_the_level_1_answer_is_a_combinator_applied_to_atoms():
    """A level-1 result is a whnf term whose arguments are unreduced
    closures with their sharing lost, so the run answers a question with
    the ABI's booleans instead of returning a numeral."""
    r = Run(READER, "level1")
    assert r.run("yes", 20_000_000) == (("Yes", None), READER_YES)
    assert r.run("no", 20_000_000) == (("No", None), READER_NO)
    assert r.run("tq", 20_000_000) == (("OQuot", None), READER_TQ)
    assert r.run("te", 20_000_000) == (("OEmpty", None), READER_TE)
    assert r.run("terr", 20_000_000) == (("RErr", None), READER_TERR)
    assert r.run("tl", 20_000_000) == (("OLogical", None), READER_TL)
    assert r.run("neg", 20_000_000) == (("No", None), READER_NEG)
    assert r.run("sym", 20_000_000) == (("OSym", None), READER_SYM)
    assert r.run("tc", 20_000_000) == (("OChar", None), READER_TC)
    assert r.run("ts", 20_000_000) == (("OStr", None), READER_TS)
    assert r.run("tz", 20_000_000) == (("OSet", None), READER_TZ)


# ---------------------------------------------------- the runs, measured

@pytest.mark.slow
@pytest.mark.parametrize("key", sorted(MEASURED))
def test_the_program_evaluates_to_six_through_the_namespace(key):
    """rp asks whether the top of the stack is 6, np whether it is 7."""
    form, text, fuel = key
    r = level1({"p": text}, ["sq"], fuel, DEFS, form, value=6)
    yes, no = MEASURED[key]
    assert r.run("rp", 100_000_000) == (("Yes", None), yes), key
    assert r.run("np", 100_000_000) == (("No", None), no), key
