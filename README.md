# SKIlark

Joy on SKIjack. A concatenative language in the line of Joy (von Thun) and
Kerby's *Theory of Concatenative Combinators*, written as one
[SKIjack](https://github.com/sigilante/SKIjack) program: its words are closed
SKI supercombinators, its programs are Scott lists of words, and its
dictionary is the program's own namespace.

The language is `skilark/programs/joy.ascii.ski` (and its Unicode spelling
beside it). The Python package only compiles it with `skijack` and reads its
data back behaviourally; `PLAN.md` says what is built, what was measured, and
what comes next.

```
pip install -e ".[test]"
python -m pytest -q
```

```python
>>> from skilark import Joy
>>> Joy().run("r1")          # 1 2 + dup +
(('RVal', [6]), 9276)
>>> Joy().run("r7")          # 3 sumto, recursion through Kerby's y
(('RVal', [6]), 110770)
```

Status: PLAN.md phase 1. The kernel is Joy's basis `dup swap pop cons cat
unit dip i` plus literals, quotations, `ifz` and `+`; eight of Joy's laws
hold on compiled terms; recursion runs through `y` with no word naming
itself. Nothing else exists yet.
