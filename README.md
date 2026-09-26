# SKIlark

Joy on SKIjack. A concatenative language in the line of Joy (von Thun) and
Kerby's *Theory of Concatenative Combinators*, written as
[SKIjack](https://github.com/sigilante/SKIjack) programs: its words are
closed SKI supercombinators, its programs are Scott lists of words or the
compositions of those words, and its dictionary is the program's own
namespace.

- `skilark/programs/kernel.ascii.ski` — the kernel: Joy's basis `dup swap
  pop cons cat unit dip i` plus `ifz`, literals, quotations and `+`, run by
  a fold over the program (`exec`, one unit of fuel per word; `execU`).
- `skilark/programs/joy.{ascii,unicode}.ski` — the kernel with a
  hand-written set of programs and Joy's laws (phase 1).
- `skilark/joy.py` — the front end. Joy text to SKIjack source in three
  forms: *interpreted* (a `prog` datum under the kernel), *compiled*
  (every word a function, a program the composition of its words,
  quotations defunctionalized, no interpreter present), and *level 1*
  (either form under SKIjack's blocking interpreter `wfN`, with
  definitions in a namespace read by scry).
- `PLAN.md` — what is built, what was measured, and what comes next.

```
pip install -e ".[test]"
python -m pytest -q              # the level-1 measurements need --runslow
python -m skilark "3 [dup +] i"
python -m skilark --define "sq == dup +" "1 2 + sq"
```

```
$ python -m skilark "3 [dup +] i"
interpreted  unfuelled      2,029  6
interpreted  fuelled        9,291  6
compiled     unfuelled        428  6
compiled     fuelled        2,993  6
```

```python
>>> from skilark import Joy, compiled
>>> Joy().run("r7")                                   # 3 sumto, by Kerby's y
(('RVal', [6]), 110770)
>>> compiled({"p": "5 sumto"}).run("up")
(('RVal', [15]), 18186)
```
