# SKIlark: Joy on SKIjack

> **Status (2026-09-25).** Phase 1 built: `skilark/programs/joy.{ascii,unicode}.ski`
> compiles on `skijack` 0.2.0 and `tests/test_joy.py` pins every number in
> §1. Phases 2–4 are plans. Where this document and the tests differ, the
> tests are authoritative.

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

## 1. Phase 1, measured

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

**The dictionary is the namespace.** At level 0 a definition is a SKIjack
equation whose value is a `prog`, spliced into a program with `cat`; the
program's own names are its dictionary and there is no lookup at run time.
At level 1 the same definitions are facts in `ns{ /over => <Then (Quote
...) ...>, ... }`, read by scry through `wfN`, and a definition `sq == dup
+` is quote-and-bind. This is the "two ways" demonstration SKIjack's
`words-to-numbers.ski` makes for three numerals, applied to a language.

**Two execution modes, one substrate.** Interpreted: `exec` folds a `prog`
datum (phase 1). Compiled: a Joy program is a composition, so `P Q`
compiles to the `B`-chain of the words' terms with no interpreter present.
The same program in both modes, with contraction counts side by side, is
the write-up's central table, and the compiled mode is what the jet census
runs over. The open question is `i` in compiled mode: a quotation that is
*code* needs a function-typed constructor field, which Stage B cannot
spell. The candidates are an untyped level-0 kernel for the compiled mode,
or a compiled mode that interprets its quotations (mixed mode). Phase 2
decides by measurement.

**I/O is events, not `key emit`.** A SKIlark machine is a state (a stack and
a dictionary) poked with events and emitting effects, the shape of
SKIjack's `kernel-events.ski`: `poke : state -> event -> [state' effects]`.
There are no memory-mapped words.

**The algebra is the test suite.** Joy's laws hold of compiled terms and
are checked behaviourally (§1). Each law is later a proof obligation on the
jet that replaces the word on its left.

## 3. Phases

**Phase 1: the kernel.** Done; §1.

**Phase 2: the compiled mode and the namespace.** Compile a `prog` to the
`B`-chain of its words' terms, settle `i` (above), and measure the nine
programs against the interpreted mode. Then level 1: the dictionary as
`ns{...}`, definitions as quote-and-bind, resolved by scry through `wfN`.
Source text to words reuses SKIjack's `parse-chars.ski` and
`ascii-digits.ski`. Exit: `1 2 + dup +` as a character string evaluates to
6 through the namespace, with its contraction count beside the level-0
interpreted and compiled counts.

**Phase 3: the census.** Run SKIjack's `avon/bench/jets.py` over the phase
1 and 2 workloads in both modes. Report the top subterms and compare the
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
- **Splice is linear in the quotation.** Every `Do`, `Dip` and `Ifz`
  copies its quotation before the continuation. Phase 3 measures this
  against CPS; the kernel is small enough to write both.
- **Fuel dominates the counts.** `1 2 + dup +` costs 1,923 contractions
  without fuel and 9,276 with it; the numeral is forced lazily at each
  word. Phase 3 should try fuel as a Church numeral or a cheaper
  decrement before comparing modes.
- **Closed sums.** `item` and `word` are fixed at compile time; extending
  either is a re-compile, as extending SKIjack's `term5` is. That is the
  intended story and the write-up says so before a reviewer does.
- **`I` is reserved.** Joy's `i` is `Do`; Kerby's `k` is `kComb`, `y` is
  `yComb`.
- **The name.** SKIlark is a working name.

## 5. Acceptance

Phase 1: `tests/test_joy.py` green on `skijack` 0.2.0 in both lexicons.
Phase 2: the nine programs run in both modes and through the namespace,
with counts pinned. Phase 3: the census table is here and in SKIjack's
`RUNTIME-DESIGN.md` §8.
