"""The example programs (examples/*.joy): whole Joy files, run as the
reference runs them, each term on the stack the terms before it left and
the top printed after each.  examples/NAME.out is what the reference
prints; joyref's model gives it, and SKIlark, interpreted, must too.
Each file is its own test, and its own program set."""

import pathlib

import pytest

import joyref
from skilark import joyfile

EXAMPLES = sorted((pathlib.Path(__file__).resolve().parent.parent / "examples").glob("*.joy"))


def _want(path):
    return path.with_suffix(".out").read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_the_model_prints_what_the_example_says(path):
    assert joyref.Joy().run_file(path.read_text(encoding="utf-8")) == _want(path)


@pytest.mark.slow
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_skilark_prints_what_the_reference_prints(path):
    """Slow: whole programs, tens of millions of contractions in copy mode,
    which the slow job runs on Avon and the reference job would check
    against aviary, in Python, at length."""
    assert joyfile.run_file(path.read_text(encoding="utf-8")) == _want(path)


def test_there_are_examples():
    assert len(EXAMPLES) >= 8


# ---------------------------------------------------------- the reader

def test_comments_definitions_and_terms():
    text = ("(* a\n comment *) DEFINE sq == dup * ; one == 1 .\n"
            "2 sq . # to the end of the line\n"
            '"a.b" size .  ' + "'. ord .")
    assert joyfile.read(text) == [("define", {"sq": "dup *", "one": "1"}),
                                  ("term", "2 sq"), ("term", '"a.b" size'), ("term", "'. ord")]


def test_an_empty_term_prints_the_top():
    assert joyref.Joy().run_file("1 2 . .") == ["2", "1"]
    assert joyfile.read("1 2 . .") == [("term", "1 2"), ("term", "")]


def test_a_term_needs_its_period():
    with pytest.raises(joyfile.JoyFileError, match="no period"):
        joyfile.read("1 2 +")


def test_the_reference_s_scoping_is_not_skilark_s():
    with pytest.raises(joyfile.JoyFileError, match="HIDE"):
        joyfile.read("HIDE x == 1 IN y == x END .")


def test_values_are_written_as_the_reference_writes_them():
    w = joyfile.write
    assert [w(("N", -3)), w(("B", True)), w(("C", 97)), w(("C", 10)), w(("T", (97, 34))),
            w(("Z", 5)), w(("L", (("N", 1), ("S", "dup"))))] == \
        ["-3", "true", "'a", "'\\n", '"a\\""', "{0 2}", "[1 dup]"]
