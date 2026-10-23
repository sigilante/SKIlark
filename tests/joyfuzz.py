"""Random Joy programs, for checking SKIlark against the reference model
beyond the pinned ones: a few values, then words and combinators with
quotations, kept when the model finishes them in 400 steps.

    python tests/joyfuzz.py SEED COUNT     # one program a line
"""

from __future__ import annotations

import random
import sys
from typing import List

import conform
import joyref

VALUES = ["0", "1", "2", "3", "-1", "-2", "true", "false", "[]", "[1]", "[1 2]", "[2 1 3]",
          "[[1] [2 3]]", "[dup]", "[true 0]", "[dup] first", "[size] first",
          "'a", "'\\000", '"ab"', '""', '"dup"', "['a \"b\"]"]
QUOTES = ["[dup]", "[pop]", "[swap]", "[1 +]", "[dup *]", "[pred]", "[succ]", "[0 =]", "[null]",
          "[small]", "[1]", "[]", "[pop true]", "[pop false]", "[+]", "[2 <]", "[first]", "[rest]",
          "[uncons]", "[dup pred]", "[*]", "[not]", "[size]", "[i]", "[[1] i]", "[stack]",
          "[ord]", "[chr]", "['a =]", "[typeof]", "[integer]", "[list]"]
WORDS = ("dup swap pop over rollup rolldown rotate dupd swapd popd id cons swons uncons unswons "
         "first rest concat size null small take drop at of + - * / rem succ pred max min abs "
         "sign neg = < > <= >= != not and or xor stack unstack i x dip ord chr has in "
         "typeof integer char logical set string list leaf user float file sametype").split()
#: combinators by how many quotations they take
COMBINATORS = {1: "nullary infra times map filter step".split(), 2: "while branch".split(),
               3: "ifte tailrec primrec fold".split(), 4: "linrec binrec genrec".split()}

#: the words whose deviations ``test_conformance.DEVIATIONS`` names: a
#: difference from the reference in a program without one is a bug
DEVIANT = {"genrec"}


def program(rng: random.Random) -> str:
    parts = [rng.choice(VALUES) for _ in range(rng.randint(1, 3))]
    for _ in range(rng.randint(1, 3)):
        r = rng.random()
        n = 0 if r < 0.5 else 1 if r < 0.7 else 2 if r < 0.8 else 3 if r < 0.9 else 4
        if n == 0:
            parts.append(rng.choice(WORDS))
        else:
            parts += [rng.choice(QUOTES) for _ in range(n)] + [rng.choice(COMBINATORS[n])]
    return " ".join(parts)


def programs(seed: int, count: int) -> List[str]:
    rng = random.Random(seed)
    out: List[str] = []
    while len(out) < count:
        p = program(rng)
        try:
            joyref.Joy(conform.OWN, steps=400).run(p)
        except (RuntimeError, RecursionError, joyref.Undefined):
            continue
        out.append(p)
    return out


if __name__ == "__main__":
    print("\n".join(programs(int(sys.argv[1]), int(sys.argv[2]))))
