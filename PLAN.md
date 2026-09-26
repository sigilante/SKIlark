# SKIlark: Joy on SKIjack

> **Status (2026-09-25).** Phases 1 and 2 built. `skilark/programs/`
> holds the kernel and the phase-1 programs; `skilark/joy.py` is the front
> end in three forms; `tests/` pins every number in §1 (the level-1 runs
> under `--runslow`). Phases 3–4 are plans. Where this document and the
> tests differ, the tests are authoritative.

*A concatenative language in the line of Joy (von Thun) and Kerby's* Theory
of Concatenative Combinators*, hosted on SKIjack: its words are SKIjack
supercombinators, its programs are Scott lists of words, and its dictionary
is the SKIjack namespace. The target is Joy's semantics, not Forth's
machine. A Joy program denotes a function from stacks to stacks,
composition is juxtaposition, quotations are lists, and there is no memory,
no return stack and no dictionary in an address space. SKI cannot offer any
of those either, so the fit is exact, and what remains is a language in
which every word is a pure closed term whose jet can be checked against the
reference reducer by extensional equality.*

## 0. What SKIlark is, and what it is not

SKIlark **is a SKIjack program**. It is written in the surface language,
compiled by `skijack` (from PyPI; this repository depends on it and adds
nothing to it), checked by Stage A and Stage B, reduced by the reference
host, and measured like every program in SKIjack's corpus. It adds no
syntax, no compiler pass and no runtime feature.

SKIlark is **Joy, not Forth**. The Forth features it omits are the ones
that follow from Forth being its own memory manager: the address space
(`@ !`), the dictionary as a linked list in that space, `STATE` and
`IMMEDIATE`, the exposed return stack (`>R R>`), `CREATE DOES>`, blocks.
Forth's minimal bootstraps (eForth's 31 primitives, sectorforth's ten,
StoneKnifeForth, milliForth) are size benchmarks, not targets, because
their primitive sets are that memory model.

SKIlark is **not a reduction machine**. SKIM, the G-machine and the
Reduceron reduce through a spine stack and their instruction sets are
stack-shaped, but that is the runtime's job and it stays in SKIjack's
`RUNTIME-DESIGN.md` and `avon/DESIGN.md`. Chuck Moore's Machine Forth and
the F18A, Bowman's J1, and Koopman's *Stack Computers: The New Wave* enter
this plan once, in §3 phase 3, as the oracle for which words hardware has
already chosen to make primitive.

The correspondence the plan rests on:

| Joy | SKIjack |
|---|---|
| the stack | Scott list: `stack === Empty \| Push item stack` |
| a word | a closed supercombinator over the stack |
| a program `P Q` | `prog === Done \| Then word prog`, or the composition `B` of the words' terms |
| a quotation `[P]` | `Quot prog`, an item on the stack |
| `i` | `Do`: pop the quotation and splice it before the continuation |
| `dip`, `cons`, `cat`, `unit` | kernel words; each re-quotes a datum with `wordOf` |
| `ifte` | `Ifz`, the Scott eliminator of `nat`: `n [Z] [S] ifz` |
| a named definition `sq == dup +` | a SKIjack equation whose value is a `prog`, spliced with `cat` |
| the dictionary | level 0: the program's own names; level 1: `ns{ /sq => <...> }` read by scry |
| a stack underflow | the `Empty` branch returns `RErr` |
| the algebra of programs | behavioural tests on compiled terms; later, jet obligations |

Kerby supplies the basis result: `{cons, sip, k}`, or the two-word
`{cake, k}`, is complete for concatenative programs, the analogue of
`{S, K}`; `k` and `y` are definable from the kernel (`k == [pop] dip i`,
`y == [dup cons] swap cat dup cons i`), so general recursion needs no
primitive and no self-naming word.

## 1. Measured

### 1a. Phase 1: the kernel

`joy.ascii.ski` is Joy's kernel, first-order: `dup swap pop cons cat unit
dip i` (as `Do`, since `I` is reserved for the combinator), literals,
quotations, `ifz` and `+`. `exec` takes fuel, one unit per word, and
returns `RTime` when it runs out. Derived words are SKIjack equations whose
values are programs. Stage A and Stage B are clean; both lexicons compile
to the same 85 terms. Sizes (atoms):

| term | atoms |
|---|---|
| `exec` (the fuelled loop, with `step` inlined) | 2,538 |
| `step` | 2,428 |
| `sumto` (`[swap [pop 0] [dup [swap i] dip 1 + +] ifz] y`) | 1,178 |
| `fuel` (the numeral 200) | 749 |
| `yComb`, Kerby's `y` | 399 |
| `over`, `tuck`, `rot`, `sip`, `kComb`, `nip` | 209, 209, 207, 199, 193, 154 |
| `wordOf`, `mul`, `cat`, `add` | 87, 77, 69, 42 |

Programs, read behaviourally with `peel` and `Prober.read_nat`; stacks are
written bottom to top:

| | Joy | contractions | result |
|---|---|---|---|
| `r1` | `1 2 + dup +` | 9,276 | `6` |
| `r2` | `3 [dup +] i` | 9,291 | `6` |
| `r3` | `1 2 over` | 11,601 | `1 2 1` |
| `r4` | `1 [2] [3] k` | 14,030 | `1 3` |
| `r5` | `1 2 unit cons` | 7,820 | `[1 2]` |
| `r6` | `+` on the empty stack | 3,385 | `RErr` |
| `r7` | `3 sumto` | 110,770 | `6` |
| `r8` | `5 sumto` | 173,876 | `15` |
| `r8starved` | `5 sumto` with fuel 10 | 4,839 | `RTime` |

Eight laws hold, each as two declared programs run to the same stack:

```
swap swap   == id            dup pop     == id
[P] i       == P             [P] [Q] cat == [P Q]
[P] [Q] dip == Q [P]         x unit      == [x]
[B] [A] k   == A             [B] [A] sip == [B] A [B]
```

`Do` is the concatenative semantics in one line: the quotation is spliced
before the continuation, `ex (cat r q) t`. `Dip` is the same splice with
the saved datum re-quoted behind it, `ex (cat r (Then (wordOf b) q)) u`.

Two findings from building it:

1. **The expander refuses mutual recursion** ("ties one fixpoint per
   equation"). `exec` and `step` are mutually recursive in the natural
   writing, so `step` takes the loop as a parameter, `step ex w q s`, and
   only `exec` is recursive. Lifting the restriction is a `skijack`
   change with its own tests, not a SKIlark task.
2. **Case branches are `;`-separated and the closing brace follows the last
   branch**; a newline before `}` is a parse error. Cosmetic, but every
   multi-branch kernel hits it.
3. **`Cons` is taken.** SKIjack finds the path type by the exact form
   `Nil | Cons seg path` and constructor names are global, so Joy's
   `cons` is the constructor `Qcons`.

### 1b. Phase 2: the front end, interpreted against compiled

`skilark.joy` parses Joy text (`3 [dup +] i`), inlines the derived words,
and emits SKIjack source in two level-0 forms. *Interpreted*: the kernel
plus each program as a `prog` datum. *Compiled*: every word a function
`stack -> result`, `seq` the composition threading the result, a program
the `seq`-chain of its words, and no interpreter present. The nine
programs, host contractions, unfuelled (`uP`) and fuelled (`rP`):

| Joy | result | interpreted | fuelled | compiled | fuelled |
|---|---|---|---|---|---|
| `1 2 + dup +` | `6` | 2,014 | 9,276 | 493 | 493 |
| `3 [dup +] i` | `6` | 2,029 | 9,291 | 536 | 3,164 |
| `1 2 over` | `1 2 1` | 2,589 | 11,601 | 626 | 3,254 |
| `1 [2] [3] k` | `1 3` | 3,250 | 14,030 | 820 | 6,074 |
| `1 2 unit cons` | `[1 2]` | 1,429 | 7,820 | 264 | 264 |
| `+` (empty stack) | `RErr` | 276 | 3,385 | 6 | 6 |
| `3 sumto` | `6` | 31,890 | 110,770 | 11,847 | 40,594 |
| `5 sumto` | `15` | 49,568 | 173,744 | 18,186 | 63,921 |

Fuel is one unit per word interpreted and one per quotation applied
compiled, so the two fuelled columns bound different things; the
unfuelled columns are the comparison, and the compiled form costs
between a quarter and a fiftieth. The compiled counts are for the
eight-program set: the case over `quot` grows with the number of static
quotations in the whole program, so `3 [dup +] i` alone costs 428.
Kernel sizes: interpreted `exec` 2,538 atoms (`execU` 2,492); compiled
`apply` 3,366 (`applyU` 3,078), `seq` 42.

**How `i` was settled.** A quotation that is *code* would need a
function-typed constructor field, which Stage B cannot spell. The compiled
form instead *defunctionalizes* (Reynolds): every static quotation in the
program is a constructor of a closed sum `quot`, whose body is that
quotation's compiled composition; `cons`, `unit` and `cat` build the three
runtime constructors `QCons item quot`, `QUnit item` and `QThen quot`
(`[P] [Q] cat == [[P] i Q]`, so `cat` is a cons onto "i, then Q", and no
constructor carries two fields of its own type, which SKIjack would take
for an object type). `apply` is the eliminator: Joy's `i` is one case
dispatch, every field stays first-order, Stage B is clean, and the
interpreted form turns out to be the same construction with `prog` as the
sum, which is why the two forms agree on every stack. A quotation is then
opaque, so the reader compares quotations extensionally, by applying
them to the empty stack, which is Joy's own notion of program equality;
all eight laws hold in both forms under that reading.

### 1c. Phase 2: level 1, the dictionary as a namespace

The third form runs either kernel under SKIjack's blocking interpreter
`wfN`. A definition named in the namespace becomes a fact, `ns{ /sq =>
<Then Dup (Then Add Done)> }` interpreted or `<seq wDup wAdd>` compiled,
and each use of the name is a scry `?^/sq` at the position the front end
wrote it. Scry paths are literals (SPEC §8: a computed path would be
reification), so names are resolved where they were written, not by a
runtime `FIND`; a scry is demand-driven, so a definition the reduction
never reaches is never read. The tokenizer is the Python front end for
the same reason: a SKIjack-side tokenizer could produce a `word` but not
a path.

Two facts of level 1 shaped the reader. At level 1 the object program
needs no fuel of its own, since the interpreter's fuel bounds the run: the
unfuelled `execU` and `applyU` are what run under `wfN`. And a level-1
result is a term in weak head normal form, so anything it carries as an
argument is an unreduced closure, and the *encoded* closure has lost its
sharing: reading the top of the stack back as a numeral cost 16 KB of
decoded term for 2, 440 KB for 5, and more than 400,000 nodes for 8. A
level-1 run therefore answers a question instead of returning a value:
`topIs v r` asks whether the top of the final stack is the numeral `v`
and answers with the ABI's booleans, `K` for yes and `K I` for no, which
are atoms alone and decode in a handful of nodes (`S` applied to atoms
names the other outcomes). Each program is asked twice, `rP` for 6 and
`nP` for 7 as the control.

`1 2 + dup +` and `1 2 + sq` (`sq == dup +` in the namespace), host
contractions on the reference reducer:

| form | program | fuel | top is 6? | top is 7? |
|---|---|---|---|---|
| interpreted | `1 2 + dup +` | 3,000 | yes, 8,796,212 | no, 8,821,207 |
| interpreted | `1 2 + sq` | 3,000 | yes, 9,477,119 | no, 9,503,122 |
| compiled | `1 2 + dup +` | 1,500 | yes, 2,328,665 | no, 2,342,964 |
| compiled | `1 2 + sq` | 1,500 | yes, 2,337,648 | no, 2,351,954 |

Beside the level-0 counts (2,014 interpreted, 493 compiled) the cost of
virtualization is four thousandfold: each emulated step walks and
rebuilds a spine of thousands of atoms, and the interpreted form pays
for its bigger term twice over. The lookup itself is cheap: `sq` through
the namespace costs 9,000 more contractions than `dup +` inline in the
compiled form and 680,000 more in the interpreted, most of that the
extra emulated steps of splicing the fact in. These runs take five
minutes (compiled) to an hour (interpreted) each on the reference
reducer and are in the suite under `--runslow`; the reader's own cases
(`test_level1.py`: yes, no, a quotation on top, an empty stack, an
error) run in seconds and are pinned. The counts are absurd on their
face and that is the point of phase 3: every emulated step is a head
structure the runtime would jet.

## 2. Design

**Data.** Five closed sums. `nat` is the prelude's Scott numeral. `item ===
Num nat | Quot prog` is the heterogeneous stack cell; adding a pair or a
string item is the surgical edit of the SKI-in-SKI paper (one constructor,
one branch in each word that inspects items). `word` is the instruction
set, `prog` is the program, `result === RVal stack | RErr | RTime`.

**Kernel.** Joy's basis and nothing else: `Dup Swap Pop Cons Cat Unit Dip
Do`, plus `Ifz`, `Lit`, `Quote` and `Add`. `exec f p s` folds `p` over `s`
under fuel `f`; `step ex w q s` dispatches on the word. Words that inspect
the stack match to the depth they need and return `RErr` from every
`Empty` branch; no word inspects `q` except `Do`, `Dip` and `Ifz`, which
splice into it. Everything Forth would call a primitive (`over rot nip
tuck sip`) is derived.

**Quotations are data, not code.** `Quot prog` holds a program, not a
function. This keeps every field first-order, so Stage B types the kernel
without a function-typed field, and it makes `Do` a splice and `cons` a
`Then`. The alternative, `Quot` holding a term applied directly, is faster
and untyped; it is the level-0 escape hatch, not the design.

**Recursion is structured.** Joy recurses through combinators (`y`,
`linrec`, `primrec`, `genrec`), all definable from the kernel by Kerby's
constructions, so no word names itself and every word stays a closed term,
the discipline SKIjack's `whnfF` equations already keep. Because `y` is
definable, fuel is mandatory and `RTime` is a value.

**The dictionary is the namespace.** At level 0 a definition is inlined
at its use by the front end (in the phase-1 file, an equation whose value
is a `prog`, spliced with `cat`); the program's own names are its
dictionary and there is no lookup at run time. At level 1 the same
definitions are facts in `ns{ /sq => <...> }`, read by scry through
`wfN`, and a definition is quote-and-bind (§1c). This is the "two ways"
demonstration SKIjack's `words-to-numbers.ski` makes for three numerals,
applied to a language.

**Two execution modes, one substrate.** Interpreted: `exec` folds a `prog`
datum. Compiled: a Joy program is a composition, so `P Q` compiles to
the `seq`-chain of the words' terms with no interpreter present, and
quotations are defunctionalized (§1b). The same program in both modes,
with contraction counts side by side, is the write-up's central table,
and the compiled mode is what the jet census runs over.

**I/O is events, not `key emit`.** A SKIlark machine is a state (a stack and
a dictionary) poked with events and emitting effects, the shape of
SKIjack's `kernel-events.ski`: `poke : state -> event -> [state' effects]`.
There are no memory-mapped words.

**The algebra is the test suite.** Joy's laws hold of compiled terms and
are checked behaviourally (§1). Each law is later a proof obligation on the
jet that replaces the word on its left.

## 3. Phases

**Phase 1: the kernel.** Done; §1a.

**Phase 2: the compiled mode and the namespace.** Done; §1b and §1c.
The exit was `1 2 + dup +` as a character string evaluating to 6 through
the namespace with its count beside the level-0 counts; the string goes
through the Python tokenizer rather than a SKIjack one, for the reason
§1c gives.

**Phase 3: the census.** Run SKIjack's `avon/bench/jets.py` over the phase
1 and 2 workloads in both forms. Report the top subterms and compare the
ranking with the J1's ALU set and the F18A's instruction set. Measure
splice (`cat`) `Do` against a CPS `exec` that sequences results instead of
copying continuations. Exit: a table here and in SKIjack's
`RUNTIME-DESIGN.md` §8, and a decision on `Do`.

**Phase 4: write-up, if the numbers justify it.** The correspondence
table, the two modes, the two-level dictionary, the census, and the laws
as jet obligations. Stack-effect typing (depth, not just shape: Diggins's
Cat, Kleffner's thesis, Mirth) is a separate thread and is not promised.
No mechanized verification of a Joy or Forth implementation is known to
this plan to cite; Kleffner's typed calculus is the nearest formal
treatment, and Joy's laws were argued on paper.

## 4. Risks

- **Mutual recursion.** The parameter workaround costs one argument per
  dispatch and reads oddly. Lifting the restriction touches `skijack`'s
  `expand.py` fixpoint tying.
- **Splice is linear in the quotation.** In the interpreted form every
  `Do`, `Dip` and `Ifz` copies its quotation before the continuation; the
  compiled form does not splice. Phase 3 measures the two against a CPS
  interpreter.
- **Fuel dominates the counts.** `1 2 + dup +` costs 1,923 contractions
  without fuel and 9,276 with it; the numeral is forced lazily at each
  word. Phase 3 should try fuel as a Church numeral or a cheaper
  decrement before comparing modes.
- **Closed sums.** `item` and `word` are fixed at compile time; extending
  either is a re-compile, as extending SKIjack's `term5` is. That is the
  intended story and the write-up says so before a reviewer does.
- **`I` and `Cons` are reserved.** Joy's `i` is `Do`, its `cons` is
  `Qcons`; Kerby's `k` and `y` are `kComb` and `yComb` in the phase-1
  file and `k`, `y` in the front end's definitions.
- **Level 1 is slow.** A thousand host contractions per emulated step
  puts the level-1 runs at minutes each; they are measured, recorded and
  gated behind `--runslow`, not run on every push.
- **The name.** SKIlark is a working name.

## 5. Acceptance

Phase 1: `tests/test_joy.py` green on `skijack` 0.2.0 in both lexicons.
Phase 2: `tests/test_modes.py` pins the eight programs and eight laws in
both forms; `tests/test_level1.py` pins the reader and, under
`--runslow`, the four namespace runs. Phase 3: the census table is here
and in SKIjack's `RUNTIME-DESIGN.md` §8.
