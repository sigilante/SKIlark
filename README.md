# SKIlark

Joy on SKIjack. A concatenative language in the line of Joy (von Thun) and
Kerby's *Theory of Concatenative Combinators*, written as
[SKIjack](https://github.com/sigilante/SKIjack) programs: its words are
closed SKI supercombinators, its programs are Scott lists of words or the
compositions of those words, and its dictionary is the program's own
namespace.

- `skilark/programs/kernel.ascii.ski` — the kernel: Joy's basis `dup swap
  pop cons cat unit dip i` plus literals, quotations and `+`, and Joy's
  next words: `- * / rem = <` on signed, unbounded integers, the truth
  values `true false` with `branch` and `ifte`, quotations as lists,
  `uncons null small`, a word in one a symbol (`[dup +] first` is `dup`),
  and the stack as data, `stack unstack`. `succ pred max min neg abs sign
  not and or > <= >= != xor first rest swons unswons concat size at of
  take drop` are derived, and so are Joy's combinators, `nullary infra
  times while tailrec linrec binrec genrec primrec map filter step fold`;
  run by a fold over the program (`exec`, one unit of fuel per word, the
  fuel the Church numeral 1,000; `execU`, no fuel). SKIlark grows toward
  Joy in full, in stages (`PLAN.md` §3), and Joy's behaviour is the
  reference implementation's: `tests/joyref.py` models it, and the tests
  check every pinned outcome against the model, but for nine deviations
  pinned with their reasons. `basis.ascii.ski` is the basis alone, with
  SKIlark's own `ifz`, as phase 3 measured it.
- `skilark/programs/joy.{ascii,unicode}.ski` — the kernel with a
  hand-written set of programs and Joy's laws (phase 1).
- `skilark/joy.py` — the front end. Joy text to SKIjack source in three
  forms: *interpreted* (a `prog` datum under the kernel), *compiled*
  (every word a function, a program the composition of its words,
  quotations defunctionalized, no interpreter present), and *level 1*
  (either form under SKIjack's blocking interpreter `wfN`, with
  definitions in a namespace read by scry).
- `skilark/zk.py` — predicates in zero knowledge: a Joy program as the
  verifier of a predicate over literal bits, which lean-ski's composed
  circuit proves. `split` adds two hidden bit strings and compares the sum
  with `x`; `python -m skilark.zk 8` writes its SKIjack source, which
  lean-ski compiles and proves. The pipeline is sound; the statement is
  weak, not yet a range proof (`PLAN.md` §3 says why). `csplit` adds a
  knapsack commitment to `a` (`python -m skilark.zk csplit 8 8`): the
  shape of a committed range proof, at toy sizes.
- `skilark/variants.py` — phase 3's measurements: the kernel with its
  loop (the splice, a continuation stack, results sequenced) or its fuel
  (computed, literal, Church) replaced, on the phase-2 programs
  (`python -m skilark.variants`). Church fuel cut a fuelled run to a
  quarter and is now the kernel's; the splice stays (`PLAN.md` §3).
- `PLAN.md` — what is built, what was measured, and what comes next.

```
pip install -e ".[test]"
python -m pytest -q              # the level-1 measurements need --runslow
python -m skilark "3 [dup +] i"
python -m skilark --define "sq == dup +" "1 2 + sq"
python -m skilark "5 fact"                # by ifte and Kerby's y
python -m skilark "-7 2 / -7 2 rem"       # -3 -1, as C truncates
python -m skilark "[1 2 3 4] 2 take size" # 2
python -m skilark "[1 2 3] [dup *] map"   # [1 4 9]
python -m skilark "5 [1] [*] primrec"     # 120
```

```
$ python -m skilark "3 [dup +] i"
interpreted  unfuelled      4,268  6
interpreted  fuelled        4,257  6
compiled     unfuelled        428  6
compiled     fuelled          442  6
```

Every reduction runs through SKIjack, by default in Python on
`aviary-kernel`'s algorithm.  [Avon](https://github.com/sigilante/avon), a
C runtime, runs the same reductions: build it (`make` in an Avon checkout),
then

```
export AVON=/path/to/avon/build/avon
python -m skilark --reducer avon  "3 [dup +] i"    # reduced by Avon
python -m skilark --reducer check "3 [dup +] i"    # by both, compared
SKIJACK_REDUCER=avon python -m pytest -q --runslow  # the suite, on Avon
```

Avon runs in its copy mode, the reference host's algorithm, so every
contraction count above, and every one the tests pin, is the same on both.
The reducer switch is SKIjack's (`SKIJACK_REDUCER`), from skijack 0.2.1,
which SKIlark requires.

```python
>>> from skilark import Joy, compiled
>>> Joy().run("r7")                                   # 3 sumto, by Kerby's y
(('RVal', [6]), 29641)
>>> compiled({"p": "5 sumto"}).run("up")
(('RVal', [15]), 27453)
```
