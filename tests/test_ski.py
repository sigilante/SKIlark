"""--ski: a program as the closed S, K, I term it runs as, which Avon
reduces from a file the same as SKIjack's reducer does."""

import os
import re
import subprocess
import sys

import pytest

from skilark.__main__ import main


def test_a_small_program_prints_as_s_k_and_i(capsys):
    assert main(["--ski", "--form", "compiled", "1 2 +"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert re.match(r"compiled: [\d,]+ atoms as a tree, [\d,]+ nodes shared", out[0])
    term = out[1]
    assert set(term) <= set("SKI ()") and term.count("(") == term.count(")")
    assert out[-1].startswith("reduces in") and out[-1].endswith(" 3")


def test_an_interpreted_program_is_its_kernel_and_its_datum(capsys):
    assert main(["--ski", "1 2 +"]) == 0
    head = capsys.readouterr().out.splitlines()[0]
    atoms = int(re.match(r"interpreted: ([\d,]+) atoms", head).group(1).replace(",", ""))
    assert atoms > 70_000                       # step alone is about 75,000


@pytest.mark.skipif(not os.environ.get("AVON"), reason="needs AVON, an avon binary")
@pytest.mark.parametrize("ext", [".skit", ".dag"])
def test_avon_reduces_the_written_term_as_skijack_does(tmp_path, capsys, ext):
    path = tmp_path / ("p" + ext)
    assert main(["--ski", "--form", "compiled", "--ski-out", str(path), "2 3 * 1 +"]) == 0
    out = capsys.readouterr().out
    steps = int(re.search(r"reduces in ([\d,]+) contractions", out).group(1).replace(",", ""))
    args = [os.environ["AVON"], "reduce", "--strategy=copy", "--whnf", str(path)]
    if ext == ".dag":
        args.insert(-1, "--dag")
    got = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    assert got.split()[:2] == ["WHNF", str(steps)]
