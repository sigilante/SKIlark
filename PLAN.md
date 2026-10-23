# SKIlark: Joy on SKIjack

> **Status (2026-10-23).** Phases 1–3 built; predicates in zero
> knowledge (§3) built; Joy in full under way, stages 1 and 2 built
> (arithmetic and comparison on naturals, truth values, `branch`, `ifte`).
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
| `1 2 + dup +` | `6` | 3,514 | 3,503 | 493 | 493 |
| `3 [dup +] i` | `6` | 3,493 | 3,482 | 536 | 550 |
| `1 2 over` | `1 2 1` | 4,590 | 4,562 | 626 | 640 |
| `1 [2] [3] k` | `1 3` | 5,860 | 5,807 | 820 | 848 |
| `1 2 unit cons` | `[1 2]` | 2,570 | 2,566 | 264 | 264 |
| `+` (empty stack) | `RErr` | 539 | 553 | 6 | 6 |
| `3 sumto` | `6` | 50,935 | 48,686 | 11,847 | 11,508 |
| `5 sumto` | `15` | 78,023 | 73,102 | 18,186 | 17,413 |

The interpreted columns are the kernel with Joy's stages 1 and 2 (§3).
On the basis kernel alone (`programs/basis.ascii.ski`), which §3's
measurements run, they were 2,014 to 49,568 unfuelled and 2,003 to
44,647 fuelled: a `word` of 26 constructors and an `item` of three make
every dispatch dearer, by 57% to 95% here. The compiled columns are
unchanged, since a program with no truth value compiles as before.

Fuel is one unit per word interpreted and one per quotation applied
compiled, so the two fuelled columns bound different things. With Church
fuel a fuelled run costs about what the unfuelled one does: up to 28
contractions more on the short programs, which pay for the numeral and
save little a word, and up to 10% less on the longest, where an
unfolding is cheaper than `execU`'s recursion. The unfuelled columns are
the comparison, and the compiled form costs
between a quarter and a ninetieth. The compiled counts are for the
eight-program set: the case over `quot` grows with the number of static
quotations in the whole program, so `3 [dup +] i` alone costs 428.
Kernel sizes: interpreted `exec` 8,564 atoms (`execU` 8,568; on the
basis, 2,488 and 2,492); compiled `apply` 3,074 (`applyU` 3,078), `seq`
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
| interpreted | `1 2 + dup +` | 5,000 | yes, 21,155,761 | no, 21,191,319 |
| interpreted | `1 2 + sq` | 5,000 | yes, 22,060,615 | no, 22,097,181 |
| compiled | `1 2 + dup +` | 1,500 | yes, 2,328,665 | no, 2,342,964 |
| compiled | `1 2 + sq` | 1,500 | yes, 2,337,648 | no, 2,351,954 |

Beside the level-0 counts (3,514 interpreted, 493 compiled) the cost of
virtualization is five to six thousandfold: each emulated step walks and
rebuilds a spine of thousands of atoms, and the interpreted form pays
for its bigger term twice over. The interpreted rows are the kernel with
Joy's stages 1 and 2, whose larger `step` needs 5,000 units of the
interpreter's fuel where the basis needed 3,000 (and took 8,796,212 and
9,477,119). The lookup itself is cheap: `sq` through the namespace costs
9,000 more contractions than `dup +` inline in the compiled form and
900,000 more in the interpreted, most of that the extra emulated steps
of splicing the fact in. These runs take minutes (compiled) to hours
(interpreted) each on the reference reducer and well under a minute on
Avon, and are in the suite under `--runslow`; the reader's own cases
(`test_level1.py`: yes, no, a quotation on top, an empty stack, an
error, a truth value on top) run in seconds and are pinned. The counts are absurd on their
face and that is the point of phase 3: every emulated step is a head
structure the runtime would jet.

## 2. Design

**Data.** Five closed sums. `nat` is the prelude's Scott numeral. `item ===
Num nat | Quot prog` is the heterogeneous stack cell; adding a pair or a
string item is the surgical edit of the SKI-in-SKI paper (one constructor,
one branch in each word that inspects items). `word` is the instruction
set, `prog` is the program, `result === RVal stack | RErr | RTime`.

**Kernel.** Joy's basis, `Dup Swap Pop Cons Cat Unit Dip Do`, plus `Ifz`,
`Lit`, `Quote` and `Add`, growing toward Joy in full: stages 1 and 2 add
`Mul Succ Pred Max Min Eql Lt`, truth values (`Truth`), `And Or Not`,
`Branch` and `Ifte` (§3). `programs/basis.ascii.ski` keeps the basis
alone, as phase 3 measured it. `exec f p s` folds `p` over `s`
under fuel `f`, a Church numeral applied to the loop's body; `step ex w q
s` dispatches on the word. Words that inspect
the stack match to the depth they need and return `RErr` from every
`Empty` branch; no word inspects `q` except `Do`, `Dip`, `Ifz`, `Branch`,
`Ifte` and `Choose`, which splice into it. Everything Forth would call a primitive (`over rot nip
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
and `k` are (`x y >` is `y x <`, `!=` is `= not`, `xor` is `!=`). The
choices:

- *Naturals still.* Joy's integers are signed and SKIlark's are unary
  naturals, so `pred` of 0 is an error and `-` waits for a signed
  representation; nothing here depends on the choice.
- *Truth values are a third kind of item*, `Logical logical` beside
  `Num` and `Quot`. Joy distinguishes them from numbers, so `1 true =`
  and `true 1 *` are errors, not coercions.
- *`ifte` restores the stack.* `[B] [T] [F] ifte` runs B, then T or F on
  the stack as it was before B: the interpreted kernel splices B before
  an internal word `Choose v r f` that holds the saved stack, and the
  compiled form runs B to its result and selects. `1 [pop true] [2] [3]
  ifte` leaves `1 2`.
- *The compiled form carries truth values only where a program uses
  them.* A third item constructor changes every term that cases on an
  item, so a program with no truth word compiles exactly as before: the
  eight programs of §1b keep their counts and zk's verifiers keep their
  terms (`vsplitB` 23,475 atoms, `vcsplitB` 53,597), which lean-ski's
  circuits prove.

The interpreted kernel's `word` has 26 constructors and its `step` 8,504
atoms, against 12 and 2,428 on the basis; every interpreted dispatch
costs more (§1b). Twenty-six programs and thirteen laws pin the words in
both forms, among them `5 fact` (by `ifte` and Kerby's `y`) at 100,268
contractions interpreted and 23,606 compiled.

## 4. Risks

- **Mutual recursion.** The parameter workaround costs one argument per
  dispatch and reads oddly. Lifting the restriction touches `skijack`'s
  `expand.py` fixpoint tying.
- **Splice is linear in the quotation.** In the interpreted form every
  `Do`, `Dip` and `Ifz` copies its quotation before the continuation; the
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
  arguments, and `Choose`, three fields of a 26-way sum, takes 29. That is the
  intended story and the write-up says so before a reviewer does.
- **`I` and `Cons` are reserved.** Joy's `i` is `Do`, its `cons` is
  `Qcons`; Kerby's `k` and `y` are `kComb` and `yComb` in the phase-1
  file and `k`, `y` in the front end's definitions.
- **Level 1 is slow.** A thousand host contractions per emulated step
  puts the level-1 runs at minutes each on the reference reducer; they
  are measured, recorded and gated behind `--runslow`, not run on every
  push. On Avon (`SKIJACK_REDUCER=avon`) the whole suite, these runs
  included, takes 48 s.
- **The name.** SKIlark is a working name.

## 5. Acceptance

Phase 1: `tests/test_joy.py` green on `skijack` 0.2.1 in both lexicons.
Phase 2: `tests/test_modes.py` pins the eight programs and eight laws in
both forms; `tests/test_level1.py` pins the reader and, under
`--runslow`, the four namespace runs. Phase 3: the census table is here
and in SKIjack's `RUNTIME-DESIGN.md` §8, and `tests/test_variants.py`
pins the loop and fuel variants behind the decisions on `Do` and fuel.
