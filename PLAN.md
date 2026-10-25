# SKIlark: Joy on SKIjack

> **Status (2026-10-24).** Phases 1–3 built; predicates in zero
> knowledge (§3) built; Joy in full under way, stages 1 to 7 built
> (arithmetic and comparison on signed integers, truth values, `branch`,
> `ifte`, quotations as lists with words as symbols, the stack as data,
> the recursion combinators, characters, strings and sets, `typeof` and
> the type tests; `ifz` retired), every word checked against the
> reference implementation (§3, stage 4), with one deviation left
> (`genrec`). `word` has 30 constructors, under Avon's cap of 32
> arguments: stage 6 merged the literals to make room (§3, stage 6), and
> stage 8 puts further kernel words in `ext`, a sum of their own.
> `skilark/programs/` holds the kernel, the basis kernel phase 3 measured
> and the phase-1 programs; `skilark/joy.py` is the front end in three
> forms; `skilark/variants.py` is the basis kernel's loop and fuel in
> variants; `tests/` pins every number in §1 and §3 (the level-1 runs
> under `--runslow`). Phase 3 closed with a decision on `Do` and one on
> fuel, and the kernel's fuel is now a Church numeral; Phase 4 is a short
> write-up.
> Where this document and the tests differ, the tests are authoritative.

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
| `ifte` | `Ifte`: run the test, restore the stack, splice the branch (the basis had `Ifz`, the Scott eliminator of `nat`: `n [Z] [S] ifz`) |
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
returns `RTime` when it runs out. The fuel is a Church numeral: `exec f`
is `f loop timeout`, the loop's body applied `f` times, so nothing is
decremented (§3 measures why). Derived words are SKIjack equations whose
values are programs. Stage A and Stage B are clean; both lexicons compile
to the same 88 terms. Sizes (atoms):

| term | atoms |
|---|---|
| `exec` (the fuelled run, with `loop` and `step` inlined) | 2,488 |
| `loop` (one word, the next level a parameter) | 2,478 |
| `step` | 2,428 |
| `sumto` (`[swap [pop 0] [dup [swap i] dip 1 + +] ifz] y`) | 1,178 |
| `yComb`, Kerby's `y` | 399 |
| `over`, `tuck`, `rot`, `sip`, `kComb`, `nip` | 209, 209, 207, 199, 193, 154 |
| `fuel` (the Church numeral 200), `twenty`, `ten` | 147, 99, 46 |
| `wordOf`, `cat`, `add` | 87, 69, 42 |

Programs, read behaviourally with `peel` and `Prober.read_nat`; stacks are
written bottom to top:

| | Joy | contractions | result |
|---|---|---|---|
| `r1` | `1 2 + dup +` | 2,003 | `6` |
| `r2` | `3 [dup +] i` | 2,018 | `6` |
| `r3` | `1 2 over` | 2,561 | `1 2 1` |
| `r4` | `1 [2] [3] k` | 3,197 | `1 3` |
| `r5` | `1 2 unit cons` | 1,425 | `[1 2]` |
| `r6` | `+` on the empty stack | 290 | `RErr` |
| `r7` | `3 sumto` | 29,641 | `6` |
| `r8` | `5 sumto` | 44,779 | `15` |
| `r8starved` | `5 sumto` with fuel 10 | 3,772 | `RTime` |

With the Scott numeral the kernel had until §3's measurements, the same
runs cost 9,276 to 173,876 (`r6` 3,385): fuel was most of every count.

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
   only `execU` is recursive. The fuelled `exec` recurses not at all: its
   levels are the Church numeral's unfoldings. Lifting the restriction is a `skijack`
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
| `1 2 + dup +` | `6` | 5,260 | 5,249 | 668 | 668 |
| `3 [dup +] i` | `6` | 4,912 | 4,901 | 684 | 698 |
| `1 2 over` | `1 2 1` | 5,975 | 5,947 | 700 | 714 |
| `1 [2] [3] k` | `1 3` | 7,723 | 7,670 | 968 | 996 |
| `1 2 unit cons` | `[1 2]` | 3,406 | 3,402 | 273 | 273 |
| `+` (empty stack) | `RErr` | 730 | 744 | 8 | 8 |
| `3 sumto` | `6` | 120,176 | 113,986 | 24,043 | 23,605 |
| `5 sumto` | `15` | 192,269 | 177,940 | 39,822 | 38,824 |

The counts are the kernel with Joy's stages 1 to 6 (§3), and
`sumto` is written with `ifte` and `pred`, since `ifz` has left the
kernel: `[swap [0 =] [pop pop 0] [dup pred swap [swap i] dip +] ifte]
y`. That puts integers and truth values into the compiled set too. On
the basis kernel alone (`programs/basis.ascii.ski`), which §3's
measurements run, with `sumto` by `ifz`, `1 2 + dup +` took 2,014
interpreted and 493 compiled, and `5 sumto` 49,568 and 18,186, unfuelled:
a `word` of 28 constructors, an `item` of six, a signed number and the
reference's comparison make every dispatch dearer.

Fuel is one unit per word interpreted and one per quotation applied
compiled, so the two fuelled columns bound different things. With Church
fuel a fuelled run costs about what the unfuelled one does: up to 28
contractions more on the short programs, which pay for the numeral and
save little a word, and up to 7% less on the longest, where an
unfolding is cheaper than `execU`'s recursion. The unfuelled columns are
the comparison, and the compiled form costs
between a fifth and a ninetieth. The compiled counts are for the
eight-program set: the case over `quot` grows with the number of static
quotations in the whole program, so `3 [dup +] i` alone costs 428.
Kernel sizes: interpreted `exec` 33,291 atoms (`execU` 33,295; on the
basis, 2,488 and 2,492); compiled `apply` 6,744 (`applyU` 6,748), `seq`
42.

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
| interpreted | `1 2 + dup +` | 7,000 | yes, 42,440,422 | no, 42,493,116 |
| interpreted | `1 2 + sq` | 7,000 | yes, 43,700,623 | no, 43,754,325 |
| compiled | `1 2 + dup +` | 1,500 | yes, 2,328,665 | no, 2,342,964 |
| compiled | `1 2 + sq` | 1,500 | yes, 2,337,648 | no, 2,351,954 |

Beside the level-0 counts of `1 2 + dup +` alone (5,260 interpreted,
493 compiled) the cost of virtualization is five to eight thousandfold:
each emulated step walks and rebuilds a spine of thousands of atoms, and
the interpreted form pays for its bigger term twice over. The
interpreted rows are the kernel with Joy's stages 1 to 6, whose
larger `step` needs 7,000 units of the interpreter's fuel where the
basis needed 3,000 (and took 8,796,212 and 9,477,119); the compiled
rows compute on naturals, as these programs cannot go negative, and are
the basis's. The lookup itself is cheap: `sq` through the namespace
costs 9,000 more contractions than `dup +` inline in the compiled form
and 1,214,000 more in the interpreted, most of that the extra emulated steps
of splicing the fact in. These runs take minutes (compiled) to hours
(interpreted) each on the reference reducer and well under a minute on
Avon, and are in the suite under `--runslow`; the reader's own cases
(`test_level1.py`: yes, no, a quotation on top, an empty stack, an
error, a truth value, a negative, a symbol, a character or a string on
top) run in seconds and are pinned. The counts are absurd on their
face and that is the point of phase 3: every emulated step is a head
structure the runtime would jet.

## 2. Design

**Data.** Five closed sums. `nat` is the prelude's Scott numeral. `item ===
Num nat | Quot prog` is the heterogeneous stack cell; adding a pair or a
string item is the surgical edit of the SKI-in-SKI paper (one constructor,
one branch in each word that inspects items). `word` is the instruction
set, `prog` is the program, `result === RVal stack | RErr | RTime`.

**Kernel.** Joy's basis, `Dup Swap Pop Cons Cat Unit Dip Do`, plus
`Lit`, `Quote` and `Add`, growing toward Joy in full: stages 1 to 3 add
`Sub Mul Div Rem Eql Lt` on signed integers, truth values (`Truth`),
`Branch` and `Ifte`, `Uncons Null Small` over quotations read as
lists, `Stack Unstack` and `Def`, a derived word in a quotation, and
`Glyph Text Ord Chr` for characters and strings (§3); `succ pred max
min not and or` are derived since stage 3, and Joy's recursion
combinators since stage 4. `Ifz`, the
basis's Scott eliminator of a natural, has left the kernel.
`programs/basis.ascii.ski` keeps the basis alone, with `Ifz`, as phase 3
measured it. `exec f p s` folds `p` over `s`
under fuel `f`, a Church numeral applied to the loop's body; `step ex w q
s` dispatches on the word. Words that inspect
the stack match to the depth they need and return `RErr` from every
`Empty` branch; no word inspects `q` except `Do`, `Dip`, `Branch`, `Ifte`
and `Choose`, which splice into it. Everything Forth would call a primitive (`over rot nip
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
SKIjack's `kernel-events.ski`, a door `[battery state]` (SKIjack `SPEC.md`
§4.1): `poke : kernel -> event -> [effects kernel']`, pulled by axis.
There are no memory-mapped words.

**The algebra is the test suite.** Joy's laws hold of compiled terms and
are checked behaviourally (§1). Each law is later a proof obligation on the
jet that replaces the word on its left.

**The runtime: supercombinators and data jets.** SKIlark is a client for
two runtime features, both built in SKIjack's `avon/` and not here. Every
SKIlark word is a closed term, so Avon can compile each word as a
supercombinator, and the phase 3 census ranks which ones to jet
(`RUNTIME-DESIGN.md` §8). Those are code jets, keyed by the structure of a
term that runs. A data jet is keyed instead by the shape of a value that is
only ever inspected. The first target is `nat === Zero | Suc nat`: the
numeral n is n nested `Suc` cells, and `add m n` recurses once per `Suc`
of `n`. A data jet would hold the numeral as a machine integer and run
`add`, `mul` and `wIfz`'s test natively. It would build the Scott term
only when a program inspects the numeral in a way the jet does not cover.
The obligation is a correspondence: the integer and the Scott term must
agree under every eliminator the jet claims, just as Joy's laws are
obligations on code jets. Values must also stay shared. An `S`
contraction duplicates its argument by reference, so printing a reduced
term can take space exponential in the reduction. The lean-ski zkVM
benchmark printed its results in full, and that is the likely cause of a
kernel panic on 2026-09-26. A data jet reads and writes the shared form,
never the printed one.

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

*Census (2026-09-28; rerun 2026-10-23 on Church fuel).* Avon's dynamic
census (`avon/docs/DESIGN.md` §6.7) replaces `jets.py` here: it counts
the terms a run calls, not the terms a program contains, and weighs each
by the contractions a jet on it would absorb. `python3 -m skilark.export`
writes the 41 runs; `avon census` reproduces every pinned count. Per
form, the three leading rows (each alone; rows overlap and do not add):

| form | runs | contractions | leading rows, % absorbed |
|---|---:|---:|---|
| phase 1 | 9 | 89,686 | a wrapper of `step` 46.9; `B (B S)` 29.6; `B (B (B S))` 18.5 |
| interpreted | 16 | 178,827 | a wrapper of `step` 44.7; `B (B S)` 28.2; `B (B (B S))` 17.7 |
| compiled | 16 | 64,500 | `applyK` 25.7; `B (B S)` 19.9; `B (B K)` 13.5 |

On the Scott fuel of the first run the three forms took 344,888, 432,962
and 150,548, and `λabcdef. f (a b d)` led two of them; with the fuel gone
the interpreter's dispatch leads. The compiled form runs the same eight
programs in 36% of the interpreted form's contractions. `step` accounts
for 70% of the gap: 386 calls at 207 contractions each with its wrapper,
79,902 of 114,327.

*Against the J1 and the F18A.* The hardware makes the stack words
primitive: `dup`, `drop`, `swap`, `over` are fields of one J1 instruction,
and `+`, `and`, `2*` are single F18A opcodes. In SKI the words cost almost
nothing. `Dup`, `Swap`, `Add` and `Do` are nullary constructors of
`word`, selectors 12 to 31 atoms long, called 75, 64, 60 and 53 times in
333,013 contractions; none ranks. What ranks is what the hardware
builds into its datapath instead of its opcode list:

- *the stack cell:* `Cons`/`Push`, 2,105 fires at 19 contractions;
- *instruction dispatch:* `step`, 189 contractions a word;
- *the counter:* `Suc` -- the J1's `T-1` and the F18A's `next`/`unext`
  in hardware -- fired 10,153 times on the Scott fuel and fires 416 on
  Church fuel: the fuel was 96% of it, and a counter the program need not
  keep is the cheapest jet;
- *argument plumbing:* `B (B K)`, `B (B S)`, `T`, the combinators that
  bracket abstraction leaves under binders -- what a register file or a
  stack's fixed depth makes free.

So the oracle's answer is negative for the word list and positive for
the machine: jet the representation (constructors, dispatch, counters),
not the words.

*The loop and the fuel (2026-10-23; `skilark/variants.py`).* The kernel
with one piece replaced at a time, run on the eight programs of §1b.
Host contractions, summed over the eight (`tests/test_variants.py` pins
each program):

| loop | fuel | fuelled | unfuelled |
|---|---|---:|---:|
| splice | computed (the kernel's before Church fuel) | 339,917 | 93,045 |
| splice | literal | 102,917 | |
| splice (the kernel) | Church (the kernel's) | 85,782 | |
| stack | computed | 422,374 | 123,771 |
| stack | literal | 144,380 | |
| sequenced | computed | 383,889 | 82,241 |
| sequenced | literal | 118,410 | |

The *splice* is the kernel's loop: `Do`, `Dip` and `Ifz` run `cat r q`.
The *stack* loop keeps the continuation as data, `ctl === Halt | Ret
prog ctl`, and copies nothing. The *sequenced* loop runs a quotation to
its result and the rest of the program on that result's stack. *Computed*
fuel is the Scott numeral the kernel had, `mul ten (add ten ten)`;
*literal* is the same 200 written out as `Suc`s; *Church* is no numeral
at all, the loop's body applied 200 times (`exec fuel`, the kernel's
since the decision below).

*Fuel.* Computed fuel costs more than the programs it bounds: fuelled
runs take 3.65 times the unfuelled. The numeral is computed as
it is consumed, at about 1,200 contractions a unit on `1 2 + dup +`
(7,262 for six units), against 47 a unit for the literal. Church fuel
costs nothing a unit: its fuelled runs take 0.92 of the unfuelled loop,
whose self-reference through the expander's fixpoint costs more than one
unfolding. The compiled form gives the same order, 117,770 computed,
42,284 literal and 31,722 Church against 32,778 unfuelled. Church fuel
stops a run at the same word as the Scott numeral: one unit a word and
one at `Done`, so `1 2 + dup +` needs 6 and `3 sumto` 66, and the
divergent `[dup i] dup i` stops at every bound tried.
**Decision: fuel becomes a Church numeral**, in the kernel and the
compiled form. It went in as its own change, since it re-pinned every
fuelled count and the census exports; Avon's copies of the exports
follow when its SKIlark pin moves.

*`Do`.* The splice copies the quotation it runs once, so it costs a
constant factor of the run, not an asymptotic one. `[P] i` against `P`,
unfuelled, with `P` 10, 40 and 160 words of `1 pop`, costs 1,408, 4,123
and 23,983 more: 100 to 150 contractions a word copied, beside 330 to
400 a word to run it. Neither alternative pays:

- the stack loop's `Do` costs 1,158 to 1,608 at any length, but every
  word now passes the continuation through `step` as one more argument,
  and that costs 41% a word (90,297 against 63,944 for 160 words). It
  takes 1.33 times the splice on the eight programs, 1.24 fuelled.
- the sequenced loop's `Do` costs 781 to 1,081 at any length and takes
  0.88 of the splice unfuelled. Fuelled, the fuel left must come back in
  every result: 1.13 times the splice with computed fuel and 1.15 with
  literal. Church fuel left would be a function, and the kernel keeps
  every field first-order.

**Decision: `Do` stays a splice.** With Church fuel its fuelled runs
take 85,782 contractions, a quarter of the Scott fuel's 339,917 and
below the unfuelled 93,045; the best fuelled alternative, sequenced with
literal fuel, takes 118,410.

**Predicates in zero knowledge (`skilark/zk.py`, 2026-09-29).** A Joy
program is the verifier of a predicate statement over literal bits, which
lean-ski's composed circuit proves: the hidden bits are constrained to
Scott Booleans and handed to the verifier, never a hidden term.
`vsplitB x r` decodes `2k` bits into two numbers, runs the program on the
stack `x` above them, and returns `K` itself when it leaves a nonzero
numeral; lean-ski's Lean front end compiles the whole source to the term
`skijack` gives, so its verifier checks a statement against the source.
The first predicate, `split`, adds the two numbers and compares the sum
with `x`, by `k` unrolled ripple-carry steps. `tests/test_zk.py` checks it
on every bit pattern at `k` = 2 and 3 (all 4,096 at `k = 4` were run once)
and on samples at `k = 8`. It costs 53,450 host contractions at `k = 8`,
about 6,700 per bit of `x` (3,300 per literal bit); in lean-ski's circuit, `k = 8` takes 129,965 rows
(`release/skilark/split8` there). The cost is the kernel's: unary numerals
and a quotation dispatch that grows with the program's quotations.

*Why bits, not a witness term.* The same program over a hidden term,
`vsplit x w`, can be fooled: a term answers the verifier's case analysis
however it likes, and `K (K (RVal R))`, with `R` a stack of `2k - 1`
zeros, is no stack at all and passes at `x` = 0 and 1 (pinned in the
tests).

*What it is not.* A range proof: some `a, b < 2^k` add up to every
`x < 2^k`, so an accepted proof shows only `x < 2^k`. A range proof needs
a commitment binding the hidden number to something public.

*The committed split* (`csplit`). The verifier also reads `m` random bits
`r` and checks a knapsack commitment to `a`: the public weights of `a`'s
and `r`'s set bits sum to the public `c`. The weights ride in `x`, so each
ripple step runs the same Joy tree: the kernel's quotation dispatch grows
with the program's distinct quotations, and weights in the code made each
step's tree distinct (256k host contractions against 201k). At `k = m = 8`
it costs 200,884 host contractions, and in lean-ski's circuit 471,888
rows (`release/skilark/csplit8` there). At these sizes the commitment
neither binds nor hides: the `2^16` openings map to 430 sums, none above
437, and `c = 255` alone opens to 157 values of `a`. The commitment step
closes at this toy scope: a full adder written natively in SKIjack costs
450 to 640 host contractions a bit, lean-ski's largest circuit affords
about 800 of them, and sound parameters need tens of thousands. A real
commitment needs its hash computed outside the reduction, a data jet.

**Phase 4: write-up.** The numbers justify a short one. Beside the
correspondence table, the two modes, the two-level dictionary and the
laws as jet obligations, Phase 3 gives it three measured results: the
compiled form runs the programs in about a third of the interpreted
form's contractions; on SKI the representation is what costs, since the census
ranks constructors, dispatch and counters and never the words, and
Church fuel removes three quarters of a fuelled run; and copying a
quotation is cheaper than threading a continuation, because one more
argument through `step` costs more than the copy. They are host
contractions on one small kernel, which makes a workshop paper rather
than a journal one. The kernel runs on Church fuel, so the paper's
counts are its counts. Stack-effect typing (depth, not just
shape: Diggins's Cat, Kleffner's thesis, Mirth) is a separate thread and
is not promised.
No mechanized verification of a Joy or Forth implementation is known to
this plan to cite; Kleffner's typed calculus is the nearest formal
treatment, and Joy's laws were argued on paper.

**Toward Joy in full.** SKIlark grows toward Joy's whole primitive set,
in stages, each a set of kernel words with their laws pinned in both
forms: (1) arithmetic and comparison on naturals; (2) truth values and
the conditionals; (3) lists from quotations (`first rest uncons size
null concat at take drop`); (4) the recursion combinators (`times while
linrec binrec primrec tailrec genrec map filter fold step infra`), derived
first; (5) characters, strings and sets. Floats and I/O are not planned.

*Stages 1 and 2 (2026-10-23; `tests/test_words.py`).* The kernel gains
`* succ pred max min = <` and the truth values `true false`, `and or
not`, `branch` and `ifte`; `> <= >= != xor` are derived words, as `over`
and `k` are (`!=` is `= not`, `xor` is `!=`; stage 4 rewrote `>` and
`<=`, which were `swap <` and `swap < not`). The choices:

- *Truth values are a third kind of item*, `Logical logical` beside
  `Num` and `Quot`. Joy's arithmetic refuses them, so `true 1 *` is an
  error. (Stage 2 also made `1 true =` an error; Joy's reference
  compares a truth value with a number by value, and stage 4 follows it.)
- *`ifte` restores the stack.* `[B] [T] [F] ifte` runs B, then T or F on
  the stack as it was before B: the interpreted kernel splices B before
  an internal word `Choose w` whose stack `w` is the saved stack with the
  two branches on top, and the compiled form runs B to its result and
  selects. `1 [pop true] [2] [3]
  ifte` leaves `1 2`.
- *The compiled form carries truth values only where a program uses
  them.* A third item constructor changes every term that cases on an
  item, so a program with no truth word compiles exactly as before: the
  eight programs of §1b keep their counts and zk's verifiers keep their
  terms (`vsplitB` 23,475 atoms, `vcsplitB` 53,597), which lean-ski's
  circuits prove.

*Stage 1b: signed integers (2026-10-23).* Joy's integers are signed;
SKIlark's are now `int === Pos nat | Neg nat`, a sign and a unary
magnitude, with `Neg m` for -(m+1), so zero is only `Pos Zero` and `=`
stays structural: ZigZag's sign bit as a constructor, which a unary
numeral reads in one case where ZigZag would walk it for its parity.
Speed is a data jet's to supply later, not the representation's. The
kernel gains `- / rem`; `neg abs sign` are derived (`neg` is `0 swap
-`). The choices:

- *Unbounded.* Joy's reference implementation computes in a C `long`;
  SKIlark's integers have no bound and do not wrap.
- *Division truncates toward zero, and the remainder takes the
  dividend's sign*, as C does: `-7 2 /` is -3 and `-7 2 rem` is -1.
  Division by zero is an error.
- *`ifz` is retired.* The Scott eliminator of a natural is not Joy and
  has no meaning on a negative; `sumto` is now written with `ifte`, as
  `fact` is.
- *The compiled form computes on naturals where no negative can arise.*
  Negatives come only from `- pred / rem` and negative literals, so a
  program without them gets the same answers on naturals and compiles
  as before, with `ifz` still available: zk's verifiers keep their
  terms (`vsplitB` 23,475 atoms, `vcsplitB` 53,597), and the level-1
  compiled runs their counts.

After stage 1b the interpreted kernel's `word` had 28 constructors and
its `step` 11,461 atoms, against 12 and 2,428 on the basis. `Choose`
holds the branches on its saved stack, one field, so its largest
constructor took 29 arguments, under Avon's cap of 32. Forty-eight programs and nineteen laws pin the words in
both forms (`tests/test_words.py`), among them `-7 2 / 2 * -7 2 rem +`
giving -7 and `5 fact` (by `ifte` and Kerby's `y`) at 106,228
contractions interpreted and 28,832 compiled. A count is to weak head
normal form, so a number pushed and not yet read costs nothing more on
integers; the arithmetic is paid when the reader decodes it.

*Stage 3: quotations as lists (2026-10-23).* A Joy quotation is a list,
and its elements may be words: `[dup +] first` is the symbol `dup`, and
consed back into a quotation and run, it runs `dup`. SKIlark's items gain
a fourth kind, `Sym word`, beside `Num`, `Quot` and `Logical`; Joy's
behaviour is the standard. The kernel gains `uncons null small`; `first
rest swons unswons concat size at of take drop` are derived. The
choices:

- *An element is an item.* A literal element is its value, a nested
  quotation a `Quot`, any other word a `Sym`; `wordOf` turns each back,
  so `cons`, `unit` and `dip` restore exactly what `uncons` took apart.
  `=` compares two symbols by name.
- *Joy's `null` and `small` read a number as an aggregate of its size*:
  `0 null` and `1 small` are true. `size`, `first` and the rest refuse a
  number.
- *`take` and `drop` stop at the end*, as Joy's reference implementation
  does: `[1 2] 5 take` is `[1 2]` and `[1 2] 5 drop` is `[]`. `first` of
  `[]` and `at` past the end are errors.
- *Room in the dispatch.* `succ pred max min not and or` leave the
  kernel for Joy's own definitions (`succ` is `1 +`, `max` is `over over
  < [swap pop] [pop] branch`, `and` is `not not swap [] [pop false]
  branch`), as `over`, `k` and `neg` are derived. The `not not` kept
  `and` and `or` refusing a non-truth value, as the words did (stage 4
  found the reference takes any number there). `word` falls to 24
  constructors, so the largest takes 25 arguments: seven under Avon's cap.
- *The compiled form reads lists only where a program does.* A program
  with `uncons`, `null` or `small` gets `Sym` items, every suffix of each
  static quotation hoisted as a static quotation of its own, a view
  (`viewQ`) giving each one's first element and rest, and a dispatch
  (`symRun`) that runs a symbol consed back into a quotation. `cat`'s
  `[[P] i Q]` reads as P's elements, then Q's. Every other program
  compiles as before: zk's verifiers keep their terms (`vsplitB` 23,475
  atoms, `vcsplitB` 53,597).

The interpreted kernel's `step` is 16,112 atoms, every case on an item
one branch wider. Eighty programs and twenty-five laws pin the words in
both forms, among them `A n take A n drop concat == A` and `x A cons
uncons == x A`.

*Stage 4: the stack as data and the recursion combinators (2026-10-23;
`tests/test_combinators.py`, `tests/test_conformance.py`).* The kernel
gains `stack` and `unstack`, and a word `Def` for a derived word inside a
quotation. `nullary infra times while tailrec linrec binrec genrec
primrec map filter step fold` are derived, with Joy's stack words `x id
dupd swapd popd rollup rolldown rotate`. The choices:

- *The standard is executable.* `tests/joyref.py` models Joy's reference
  implementation, Wodan58/Joy at `fe9fa0f`, the maintained descendant of
  von Thun's joy1, builtin by builtin from its C source, over the kinds
  SKIlark has. Every pinned outcome, in both forms, is the model's: 118
  programs, and the laws, checked in `test_conformance.py`. Five hundred
  random programs (`tests/joyfuzz.py`, seeds 1 and 2) in both forms
  differed from the model 33 times, each in one of the deviations below;
  sixty of them are in the suite under `--runslow`.
- *The model corrected stages 2 and 3 in five places.* A test takes any
  value as a truth value, zero and empty false and a symbol true, so `1
  [2] [3] branch` runs `[2]`. `=` and `<` are the reference's comparison:
  two null values are the same (`[] 0 =`), numbers and truth values
  compare by value (`1 true =`), symbols by name (`dup` before `swap`),
  and any other pair is unordered, greater in both orders. So `>` is not
  `swap <` (`[1] 2 >` and `2 [1] >` are both true); `>` and `<=` are now
  derived from `<` and `=`. Every negative is `small`. A derived word in
  a quotation is the symbol it names: `[size] first` is `size`, not the
  first word of its expansion. And `dip` put a symbol back by running
  it, so `[dup] first [1] dip` left `1 1`; it now leaves `1 dup`.
- *A derived word in a quotation is a `Def`.* `Def (Named name body)`
  runs as its body and reads, as an element, as the symbol `name`. At
  the top of a program or of a body, where nothing reads it, a derived
  word is still inlined. Symbols compare by name, so the kernel holds its
  words' names (`nameOf`), in a code that keeps their order: a letter is
  its place in the alphabet, an operator sign a small negative. They are
  9,340 of `step`'s 22,897 atoms.
- *The combinators take their quotations into the body `y` recurses on.*
  `linrec`'s body sees the caller's stack with its own recursion on top
  and the four quotations above it, and runs R2 after the recursion by
  splicing `R1 [rec i] R2` rather than holding R2 on the stack. `map`
  and `filter` take the caller's stack with `stack` and run each element
  on it with `infra`, as the reference runs P on the stack below the
  aggregate. `primrec` needs no type test: `0 >` is false of zero, a
  negative and the empty list and true of a non-empty list, and `dup dup
  =` tells an integer from a non-empty list, which the reference's
  comparison holds unequal to itself.
- *Deviations.* Nine programs part from the reference, each pinned with
  its reason. A derived word cannot see its argument's kind, so `[1]
  not`, `true 5 and`, `true 1 xor` and `3 true max` give values where the
  reference errs, and `true succ` and `[1 2] true take` err where it
  gives values; `true false max` gives `true` where it gives 1. (Stage 5
  closed `[1] not` with `ord`.) A derived
  combinator checks a quotation only when it runs one, and `genrec` hands
  R2 a quotation that recurses through `y`, not the reference's
  `[[[B] [T] [R1] R2] #genrecaux]`. Joy's type tests (`logical`,
  `integer`, `list`, ...) would close the first group; they are kernel
  words.
- *Fuel is 1,000 words.* The derived combinators spend tens of words a
  level: `3 [1] [*] primrec` needs 306 and `[1 2 3] [2 rem 0 =] filter`
  350, past the old 200. The compiled form's fuel, one unit per quotation
  applied, stays 200.

`word` has 27 constructors, `Def` and `Choose` with one field each, so
the largest constructor takes 28 arguments: four under Avon's cap. The
combinators are slow on unary data: `3 [1] [*] primrec` takes 320,046
contractions interpreted and 126,911 compiled, `[1 2] [dup *] map`
238,594 and 119,555, against 2,577 and 343 for `3 4 *`. The stage-3
programs cost a quarter more interpreted (`5 fact` 133,976, from
107,155). A compiled program set compiles in time that grows faster than
its static quotations, 4 s for 59 and 135 s for 170 on skijack 0.2.1,
so `test_combinators.py` compiles each program alone.

*Stage 5: characters and strings (2026-10-24; `tests/test_text.py`).* An
item is also `Char int`, a character by its code, or `Str text`, a string
by its characters' codes; the kernel gains their literals, `Glyph` and
`Text`, and Joy's `ord` and `chr`. Joy's text syntax is the reference
scanner's: `'a` is a character, `"a b"` a string, and both take the
escapes `\n \t \b \v \f \r \" \' \\` and three decimal digits
(`'\065` is `'A`). `has` and `in` are derived. The choices:

- *A character is a number to arithmetic and comparison*, as in the
  reference: `'A 1 +` is `'B`, `'a succ` is `'b`, `'A 65 =` is true,
  and `*`, `/` and `rem` refuse a character. `ord` and `chr` take a
  number, a character or a truth value.
- *The list words take strings.* `first rest uncons cons swons concat
  size at of take drop null small` and the combinators read a string as
  its characters and give strings back where the reference does: `"abc"
  2 take` is `"ab"`, `"abc" [succ] map` is `"bcd"`, and `cons` puts only
  a character onto a string. `take` makes its empty result of its
  argument's kind (`dup size drop`), and `primrec` tells an integer from
  an aggregate by `0 X <`, which is true of a positive number alone.
- *A string compares with a symbol by name*, as the reference's
  comparison reads both as C strings: `"dup" [dup] first =` is true. The
  kernel's names keep their order-keeping code and are turned into codes
  for the comparison.
- *`ord` is a guard.* `dup ord pop` errs on anything but a number, a
  character or a truth value, so `not`, `xor`, `max` and `min` now refuse
  a list or a string as the reference does.
- *Deviations.* `"ab" [ord] map` gives a string of the codes' C
  characters in the reference and errs here, since `cons` puts only a
  character onto a string. `primrec` on a character errs in the
  reference and counts down here, since `0 X <` cannot tell a character
  from an integer. The model does not follow two artefacts of
  the reference's C strings: a string ends at a character 0, and a
  character above 127 reads back negative where C's `char` is signed.
  SKIlark's strings hold any integer.
- *The compiled form has characters and strings only where a program
  does*: a character or string literal, or `ord` or `chr`, which the
  guarded words use. zk's verifiers keep their sources byte for byte.

`word` has 31 constructors, `Glyph`, `Text`, `Def` and `Choose` with one
field each, so the largest takes 32 arguments: Avon's cap. `step` is
33,231 atoms, every case on an item two branches wider, and `5 fact`
takes 154,292 contractions interpreted, from 133,976 at stage 4.
Forty-three programs and seven laws pin the words in both forms, among
them `c ord chr == c` and `S n take S n drop concat == S`.

**At the cap: sets, and what else wants a slot.** A Joy set is a set of
the integers 0 to 63, with a literal `{1 2 3}` and its own meaning for
`and or xor not` (intersection, union, symmetric difference,
complement), `<` (proper subset) and every aggregate word. It needs a literal word at least, and
the set operations in the kernel or a type test to dispatch on: one
constructor past the cap. Four other things want slots. Joy's type tests
(`logical integer char string list set`) would close the deviations of
stage 4. A kernel `genrec` would hand R2 the reference's quotation. The
other quotations a combinator never runs would be checked. The ways on:

1. *Raise Avon's cap.* `AV_JET_ARITY_MAX` sizes fixed arrays in
   `src/jets.c`, `src/reduce.c`, `src/copy.c` and `src/gc.c` and the
   jet markers in `include/avon.h`, 32 of them, which the template check
   uses (DESIGN §6.10: a template past 32 formals
   dispatches as SKI). Doubling it costs stack and a wider probe for every
   constructor; the kernel keeps its shape.
2. *Split `word` in two.* `word === ... | Ext ext`, the rarer words in
   `ext`: no ceiling, one more dispatch for each extension word, and
   every jet on `word` re-keyed.
3. *One literal constructor.* `Lit int`, `Quote prog`, `Truth logical`,
   `Glyph int` and `Text text` become `Lit item`: five constructors to
   one, four slots back, and the literals' code shared; `item` and `word`
   become directly recursive in each other.
4. *Derive `ifte`.* With `stack` and `unstack`, `[B] [T] [F] ifte` is
   `[[nullary] dip] dip branch`, so `Ifte` and `Choose` can leave: two
   slots, at the price of a stack copy for every test.

*Stage 6: the sidestep (2026-10-24).* Sets and type tests fit under the
cap with no change to Avon, in three steps: the literals merge (option
3), the kernel gains Joy's `typeof`, from which the type tests derive,
and sets arrive as an item, the cases the kernel's words take for it,
and Joy's `not`, the complement, as the kernel's 29th word.

- *One literal constructor.* `Lit int`, `Quote prog`, `Truth logical`,
  `Glyph int` and `Text text` are `Lit item`: `word` has 27
  constructors, its one-field ones take 28 arguments, and `step` is
  31,506 atoms, from 33,231. `Lit` pushes any item, a symbol too, so
  `dip` puts its item back with one `Lit` where a symbol needed a
  quotation, `uncons` and `pop`. No outcome changes, in either form.
  Every interpreted count falls: the 161 pinned programs take 9.3% fewer
  contractions in all, each from 0.67 to 0.93 of its stage-5 count
  (median 0.89); `[dup] first [1] dip`, which puts a symbol back, falls
  most. The compiled form has no `word` and keeps its counts. The level-1 runs
  fall from 40,205,700 and 41,419,680 contractions to 33,524,535 and
  34,659,638.
- *Joy's `typeof`.* The kernel's 28th constructor numbers a value's type
  as the reference's globals.h does: a user-defined symbol 2, a builtin
  3, a truth value 4, a character 5, an integer 6, a string 8, a list 9,
  and a set, which step 3 brings, 7. A `Def` is `Named` (one of Joy's) or `User` (the program's
  own, Kerby's words and the two programs among them, or one of Joy's
  names with another body), and the compiled form's user symbols are
  `U` and the name. `integer char logical set string list leaf user`
  are `typeof` and a comparison, `float` and `file` are false of every
  value SKIlark has, and `sametype` derives as sametype.c reads it: a
  builtin on top is the same type as the same builtin alone.
- *Each word checks its arguments as the reference does.* Of the ten
  deviations nine close. `and or xor max min` check that their two
  arguments are of one type (SAME2TYPES), `succ pred max min` give a
  truth value back as an integer, `take drop at of` take a truth value
  as an index, `primrec` refuses a character, and every derived
  combinator checks its quotations before it runs one, so `0 5 times`
  and `[] 5 map` err as the reference's do. `map` gives a string's
  results back as C chars, so `"ab" [ord] map` is `"ab"`. The checks
  are `typeof` and comparisons, without `ord` or a subtraction, so a
  compiled program keeps its naturals and has characters only where it
  did; the compiled form drops `map`'s string branch from a program set
  with no string literal, since only a literal makes a string. `genrec`
  stays the one deviation: its R2 sees a quotation, not the reference's
  own word.
- *What the checks cost.* `step` is 34,204 atoms. No pinned outcome
  changes. The 161 pinned programs take 15.0% more interpreted
  contractions than at step 1 (4.4% more than at stage 5) and 19.0% more
  compiled; `succ` and `pred`, which must tell a truth value from an
  integer, cost most: `5 succ` takes 9,372 interpreted and 3,183 compiled
  contractions, from step 1's 2,772 and 427, and `5 sumto` 184,099 and
  39,822, from 140,114 and 30,103. `BENCHMARKS.md` tabulates every step. The level-1 runs take 35,243,483 and
  36,399,854. Forty-six programs and six laws pin the types
  in both forms (`tests/test_types.py`), and zk's sources stay byte for
  byte.
- *Deep programs spill.* SKIjack refuses an expression whose
  applications nest more than 256 deep, and a program nests about a
  level a word, so inlined checks put a random program of a few
  combinators past it. Past 240 levels the front end makes a
  subexpression an equation of its own, of the same parameters: a
  datum's has none and costs nothing at run time, and a compiled body's
  takes `ap`. No pinned program spills; the deepest nests 174 levels. The model
  keeps integers to 64 bits, as the reference's are, and calls a result
  past them undefined, so the fuzz never squares a number without end.
- *Sets.* An item is also `Set set`, its members the integers 0 to 63,
  distinct and ascending; a literal `{3 1}` is read as the reference's
  `list2set` reads it, integers and characters 0 to 63. The kernel's
  words take sets as the reference's do: `cons` puts in a member (an
  integer or a character, 0 to 63, or an error), `uncons first rest`
  take the least, `cat concat` the union, and `null small typeof` and
  the truth value read them. `=` compares a set with a number by the
  number's 64 bits, two's complement, as compare.h does, and `<`, when
  either value is a set, is comprel.h's proper subset of the bits; `>`
  and `>=` derive that order by `swap`. `has in map filter step fold
  primrec size at of take drop` take sets as derived; `map` makes a set
  of its results.
- *`not` is the kernel's.* The complement walks 0 to 63, and a derived
  loop costs about 300,000 interpreted contractions an element: with a
  derived complement, `{1 2} not size` passed the reader's 5,000,000.
  Joy's `not` is the kernel's 29th constructor instead: logical
  negation of a number, a character or a truth value, a set's
  complement, an error otherwise. With it and the union the set
  operations derive by De Morgan: `X Y and` is `not (not X or not Y)`,
  and `xor` is `(X - Y) or (Y - X)`, each difference `not (not X or Y)`.
  The set functions merge the ascending members: `{1 2} {2 3} and
  first` takes 39,239 interpreted contractions, where a draft that built
  the union by repeated insertion took 1,593,877. `word` has 29
  constructors, its one-field ones take 30 arguments, under Avon's 32.
- *The compiled form has sets only where a program does.* A set literal
  alone makes a set, so a program set without one takes the set words
  without their set branches (`joy.PLAIN`), and its kernel keeps its
  shape; with one, the kernel gains `Set` and the lines that take it. zk's
  sources stay byte for byte.
- *What sets cost.* `step` is 45,016 atoms, from 34,204; the bits a
  comparison takes are a top-level function, so no word passes them.
  No pinned outcome changes. Over the 207 programs of steps 1 and 2 the
  interpreted counts rise 3.7% and the compiled fall 2.5%: `true not`
  takes 1,713 interpreted and 116 compiled contractions, from 17,626
  and 7,524, and `times` counts down by the kernel's `<`, so `2 [10]
  times` takes 99,463 and 17,751, from 173,598 and 33,298; `>` and `>=`
  ask whether either value is a set, so `3 3 >=` takes 24,720
  interpreted, from 6,471. Against stage 5, the 161 programs it pinned
  take 7.8% more interpreted contractions in all (median 0.97 of
  stage 5's) and 15.5% more compiled. The level-1 runs take 38,575,065
  and 39,777,702. Seventy-three programs and seven laws pin sets in
  both forms (`tests/test_sets.py`); the dearest, `{1 2 3} [2 <]
  filter`, takes 475,542 interpreted contractions.

*Stage 7: the library words (2026-10-24; `tests/test_library.py`).*
The reference's builtins that need no kernel word are derived, each
checking its arguments as the C source does and checked against the model
built from it:

- *Stack words and small ones:* `rollupd rolldownd rotated` (their words
  under `dip`), `choice`, `setsize` (64) and `enconcat`.
- *The n-ary combinators:* `app1 app11 app12 unary binary ternary unary2
  unary3 unary4 app2 app3 app4 cleave construct`. Each result is
  `nullary` of a program that drops the other arguments, so P sees the
  stack the reference gives it: the one below all its arguments.
- *The type conditionals:* `ifinteger ifchar iflogical ifset ifstring
  iflist iffloat iffile`.
- *Clauses:* `cond case opcase`, a loop over the clauses through `y`;
  `cond` checks every test is a quotation first, as cond.c does.
- *Aggregates:* `split`, `some` and `all`, which stop at the first member
  that decides, as someall.h does, and `equal`, lists member by member.
- *Trees:* `treestep treerec treegenrec`. As `genrec` does, `treerec` and
  `treegenrec` hand C a quotation that recurses through `y` where the
  reference hands it its own `#treerecaux`, so a C that looks at it sees
  three members, not two: two deviations, pinned, of `genrec`'s kind.
- *Fuel is 10,000 words.* `construct`, `equal` and `split` spend
  hundreds of words an element, past 1,000; the larger numeral adds 7
  contractions to every fuelled interpreted run, and no unfuelled count
  changes.

- *`has` keeps a symbol a value.* It put the value it looks for into a
  quotation, `[=] cons`, where a symbol runs: `[size] first [{2}] in`
  erred where the reference gives false. It goes in as `[X] first` now.
  The fuzz found it.

Eighty-three programs and seven laws pin them in both forms; the dearest,
`[1 [2 3]] [1 [2 3]] equal`, takes 2,614,403 interpreted contractions.
`compare` waits: it orders sets as the reference does, by their 64 bits
as an integer, which the kernel's sets do not hold. `name body intern
maxint` need the kernel: a symbol's name as a string, a definition's
body, a string as a symbol, and an integer of 63 bits, beyond a unary
numeral.

*Numbers on skijack's operations (2026-10-25).* The first step of Avon's
data-jet plan (its DESIGN §6.14). The kernel's naturals are skijack's
prelude operations, `natAdd natSub natMul natIfEq natIfLe`, which Avon
runs natively on numerals it holds as words but only when both operands
are words already. So each operation cases on its numerals first, a
computed one becoming a word as it is forced, and each integer operation
on its integers; the compiled form's integers do the same, and its naturals,
whose terms lean-ski proves for zk, keep their own. Division stays a
loop of subtractions until skijack has `natDiv` and `natRem`.

| program, to normal form, Avon with templates and data | before | after | operations |
|---|---:|---:|---:|
| `200 200 *` | 8,360,924 | 160,092 | 1 |
| `200 200 * 7 /` | 8,607,178 | 131,564 | 11,430 |
| `200 200 * 199 <` | 84,363 | 136 | 3 |
| `200 200 * 199 200 * -` | 16,520,814 | 962 | 4 |
| `6 fact` | 13,548 | 5,980 | 30 |
| `30 sumto` | 17,805 | 15,750 | 149 |

Without the cases, an operation on a computed number declines and runs
as its term: `200 200 * 199 200 * -` took 398,959 steps. `200 200 *`
spends what it spends printing 40,000 in unary; division here is a loop
of native subtractions and tests (11,430 of them), which the next
paragraph replaces.

On aviary, which runs the operations as their terms, no pinned outcome
changes and the 363 pinned programs take 3.5% more interpreted
contractions in all and 0.5% more compiled (each at most 1.42 of
before); `step` is 57,842 atoms, from 45,016, and the interpreted
level-1 runs take 40,555,362 and 41,794,287. A computed number reads
back slower, so the reader gives a numeral the cap it gives a constructor
(5,000,000 contractions), not skijack's 200,000.

*Division on `natDiv` and `natRem` (2026-10-25).* skijack 0.2.2 adds the
two operations (skijack #25), total as its others are (by zero, 0 and the
dividend), and Avon runs them natively (Avon #70). `divN` and `remN` case
on their numerals and call them, as the other operations do; `div2`
still refuses a zero divisor first. The kernel needs `skijack>=0.2.2`.

| program, to normal form, Avon with templates and data | before | after | operations |
|---|---:|---:|---:|
| `100 7 /` | 431 | 153 | 1 |
| `200 200 * 7 /` | 131,564 | 22,986 | 2 |
| `200 200 * 7 rem` | 108,716 | 138 | 2 |
| `0 200 200 * - 7 /` | 131,596 | 23,018 | 2 |

`200 200 * 7 /` spends the rest building 5,714 in unary. On aviary no
pinned outcome changes; the three programs that divide (`2 rem` in
`filter` and `split`) take 0.2% to 0.4% fewer contractions in each form,
and `step` is 57,570 atoms, from 57,842.

*Stage 8: the kernel's further words in `ext` (2026-10-25).* `word` had
29 constructors of the 31 Avon's cap allows, and each word the kernel
takes over from a derivation would spend one. Stage 8 spends one on all
of them: `Ext ext` is `word`'s thirtieth constructor, and `ext`, a sum
of its own, holds the kernel's further words, up to 31. The first are
`size` and `at`, the list words Avon's data jets will take next; `step`
cases on `Ext` and `exts` on the `ext`, one dispatch more for these
words than for `word`'s own. A word in a quotation is read back as its
name, `[size] first` the symbol `size`, of `typeof` 3, as before. The
compiled form has no `word` sum and keeps deriving them, and a program's
own `size` or `at` stays its own (`joy.kernel_defs`).

`size` counts an aggregate's members and `at` takes the member at an
index, an integer or a truth value, as the derivations did, and errs
where they erred. Interpreted, on Avon:

| program | derived | `ext` |
|---|---:|---:|
| `[1 2 3] size` | 82,459 | 1,895 |
| `{1 5 9} size` | 82,249 | 1,885 |
| `[4 5 6] 1 at` | 115,061 | 3,364 |
| `"abc" 2 at` | 163,493 | 3,610 |
| `[[1 2] [3]] [size] map` | 508,279 | 374,049 |
| `[size] first` | 2,547 | 2,633 |

No pinned outcome changes. The 363 pinned interpreted programs take
10.6% fewer contractions at the geometric mean, and 46,528,801 in all,
from 48,183,315; those that use `size` or `at` up to 58 times fewer, and
those that use neither up to 3.8% more, a case on a wider `word`. `step`
is 61,675 atoms, from 57,570, and the interpreted level-1 runs take
42,440,422 and 43,700,623, 4.6% more. The compiled form is unchanged.

Then `size` and `at` moved onto skijack 0.2.3's `listLength` and `listAt`
(skijack #27, #28), which Avon runs natively on lists it holds whole
(Avon #74); `at` tests its index against the length first, so it still
errs past the end. On Avon with templates and data jets, to normal form:

| program | own recursion | `listLength`, `listAt` |
|---|---:|---:|
| `[1 2 3 4 5 6 7 8 9 10 11 12] size` | 216 | 121 |
| `[1 2 3 4 5 6 7 8 9 10 11 12] 9 at` | 223 | 138 |
| `"hello, world" 7 at` | 638 | 571 |
| `{1 3 5 7 9 11 13} size` | 161 | 101 |

As terms, on aviary, no pinned outcome changes; six pinned programs move
by under 1%, and `step` is 61,918 atoms, from 61,675.

*Stage 9: the pure words left (2026-10-25; `tests/test_pure.py`).* Of the
reference's 227 builtins SKIlark had 123; of the 104 left, 12 need
neither I/O, floats nor the interpreter's own state. Six come in here,
each modelled in `joyref` from its C source and pinned in both forms:

- `div` is `over over rem [/] dip`, `rem`'s checks first, as div.c makes
  them.
- `pick` takes its index among four parameters, past the stack the last
  item and negative the top (pick.c), through `stack` and `at`.
- `compare` is ext's `Compare` and the compiled form's `wCompare`: the
  comparison `=` makes, as -1, 0 or 1, but with a set and a number or set
  by their bits as a signed 64-bit integer, member 63 its sign
  (compare.h), where `<` compares sets by subset. It costs 2,718
  contractions interpreted whatever it compares.
- `condnestrec` and `condlinrec` (condnestrec.c) choose the first clause
  whose test holds on the stack as it was, else the last clause whole,
  and run its parts with the recursion between any two: derived as the
  parts spliced around `[clauses self i]` under `y`.
- `casting` (casting.c) takes X's value as its num field holds it under
  the type Y, among truth values, characters, integers and sets, which
  share that field; the reference reinterprets other values' bytes, which
  the model leaves undefined. A chain of `branch`es, not `cond`, keeps it
  to 50,000 to 570,000 contractions, from 2.9 to 4.2 million.

`maxint` is the reference's 2^63 - 1, which SKIlark's unary integers
cannot hold, and stays out. `name`, `intern` and `body` (symbols and
their names as strings) and `strtol` and `format` (numbers to and from
text) are the next two steps. No pinned outcome elsewhere changes; 27
programs take up to 2.8% more, and `step` is 68,549 atoms, from 61,918,
with the signed set order.

*Stage 10: symbols and their names (2026-10-25; `tests/test_symbols.py`).*
`name`, `body` and `intern` are ext's `Name`, `Body` and `Intern`, each
modelled from its C source:

- `name` (name.c) gives a symbol's nickname, an operator's spelled as
  optable.c spells it (`+` is `"plus"`, `>=` `"geql"`), and a literal's
  type's name (`5 name` is `"integer type"`).
- `body` (body.c) gives a user definition's body as a quotation of its
  symbols; any other symbol has none, and errs.
- `intern` (intern.c) reads a string as Joy's reader would, a name and
  not a number nor a string with a space or one of `"#'().;[]{}` past
  its first character, and gives that name's word: a kernel word, an ext
  word, a derived word as its `Def`, or the program's own definition,
  and a name it does not know a user symbol with no body, which runs as
  nothing, as the reference's undefined symbol does (`undeferror` is 0).

Names change their code for it: each character is its code less 96,
which keeps the letters' codes and the order of names and, unlike the
operators' old code, holds any character, so `"Zork" intern name` is
`"Zork"`. `intern` is the interpreted form's alone, as decided: its table
holds every Joy word, and the compiled form's symbols are the program's
own, so a compiled program that interns is refused. `name`'s and
`intern`'s machinery (`programs/names.ascii.ski`) and intern's table, a
binary search over about 140 names, come only with a program that uses
them: `step` is 73,692 atoms, from 68,549; 131,171 with `name`; 1.67
million with `intern`, whose programs take 25,000 to 2.3 million
contractions and whose tests raise the reader's probe cap. The compiled
form's `name` and `body` read the program's own symbols, `body` a static
quotation of each user definition it quotes. No pinned outcome elsewhere
changes; 47 programs take up to 4.5% more.

*Stage 11: numbers to and from text (2026-10-25; `tests/test_numtext.py`).*
`strtol` and `format` are ext's `Strtol` and `Format` in both forms, on
`programs/numtext.ascii.ski`, which a program set carries only when it
uses one, written in skijack's numeral and list operations so that one
text serves both forms:

- `strtol` (strtol.c) reads as glibc's `strtoll(s, 0, b)`: spaces, a
  sign, base 0 reading `0x` and a hex digit as 16 and a leading 0 as 8,
  the digits to the first that is not one; a base past 36, 1 or negative
  gives 0.
- `format` (format.c) writes printf's `%*.*lld` with its conversion
  among `d i o x X`: a negative width left-justifies, a negative
  precision is 1, and 0 at precision 0 has no digits. A negative number
  under `o`, `x` or `X` is its 64 bits, which the model leaves undefined.

Derived in Joy first, they were too dear: each walks strings with list
words, which turns on the compiled form's list views, so one compiled
program took 40 seconds to compile into an 84-million-atom term, and
`"12" 10 strtol` 724,264 contractions; as kernel words, 0.3 seconds and
235. The core is written for a reducer that shares nothing, as the
tests' copy mode is: a value used twice is computed twice, so each text
is read once in one pass, the base and the digit table are cased to
literals before use, and the digits carry their count forward. A
format's result is pinned by comparison with the reference's string,
not read back, since an interpreted string is read a probe a character.
No pinned outcome elsewhere changes; 67 programs take up to 5.7% more,
and `step` is 75,650 atoms, from 73,692.

## 4. Risks

- **Mutual recursion.** The parameter workaround costs one argument per
  dispatch and reads oddly. Lifting the restriction touches `skijack`'s
  `expand.py` fixpoint tying.
- **Splice is linear in the quotation.** In the interpreted form every
  `Do`, `Dip`, `Branch` and `Ifte` copies its quotation before the continuation; the
  compiled form does not splice. Measured in §3: 100 to 150 contractions
  a word copied, a constant factor of running it, and both alternatives
  cost more. The splice stays.
- **Fuel dominated the counts.** `1 2 + dup +` cost 2,014 contractions
  without fuel and 9,276 with the Scott numeral, computed as it was
  consumed. The kernel's Church fuel brings it to 2,003 (§3), so fuelled
  and unfuelled counts now differ by at most 10%; the modes still compare
  unfuelled, since their fuels bound different things.
- **Closed sums.** `item` and `word` are fixed at compile time; extending
  either is a re-compile, as extending SKIjack's `term5` is. Each Joy
  word added re-pins every interpreted count, and the sums cannot grow
  without bound in Avon's terms: its constructor jets take at most 32
  arguments, and the largest, the one-field constructors of a 31-way
  sum, take 32: the cap. Stage 3 made room by deriving seven words,
  stage 4 derived its thirteen combinators, and stage 6 merged the five
  literals into one, leaving `word` at 28 constructors with `typeof`
  (§3, stage 6).
  That is the
  intended story and the write-up says so before a reviewer does.
- **`I` and `Cons` are reserved.** Joy's `i` is `Do`, its `cons` is
  `Qcons`; Kerby's `k` and `y` are `kComb` and `yComb` in the phase-1
  file and `k`, `y` in the front end's definitions.
- **Level 1 is slow.** A thousand host contractions per emulated step
  puts the level-1 runs at minutes each on the reference reducer; they
  are measured, recorded and gated behind `--runslow`, not run on every
  push. On Avon (`SKIJACK_REDUCER=avon`) the whole suite, these runs
  included, takes 1,230 s.
- **The name.** SKIlark is a working name.

## 5. Acceptance

Phase 1: `tests/test_joy.py` green on `skijack` 0.2.1 in both lexicons.
Phase 2: `tests/test_modes.py` pins the eight programs and eight laws in
both forms; `tests/test_level1.py` pins the reader and, under
`--runslow`, the four namespace runs. Phase 3: the census table is here
and in SKIjack's `RUNTIME-DESIGN.md` §8, and `tests/test_variants.py`
pins the loop and fuel variants behind the decisions on `Do` and fuel.
