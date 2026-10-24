# Benchmarks

What stage 6 (PLAN.md §3), the sidestep at Avon's cap, cost and saved,
measured at four commits:

| label | commit | what it adds |
|---|---|---|
| stage 5 | `eb90896` | characters and strings; `word` at the cap |
| step 1 | `d5b5625` (#11) | the five literal constructors become `Lit item` |
| step 2 | `2af0696` (#12) | Joy's `typeof`, the type tests, the argument checks |
| step 3 | `a53dc73` (#13) | sets and the kernel's `not` |

**Method.** Every count is host contractions on aviary, the reference
reducer, under skijack 0.2.1, to the weak head normal form of the result,
unfuelled (`uP`). The pinned tables in `tests/test_*.py` are these
numbers, so `python -m pytest` at a commit reproduces its column. Words
and modes compile their programs as one set; combinators, text, types
and sets compile each program alone. Avon reduces to the same counts.

## The kernel

| | stage 5 | step 1 | step 2 | step 3 |
|---|---:|---:|---:|---:|
| `word` constructors | 31 | 27 | 28 | 29 |
| arguments of a one-field `word` constructor | 32 | 28 | 29 | 30 |
| `item` constructors | 6 | 6 | 6 | 7 |
| `step`, atoms | 33,231 | 31,506 | 34,204 | 45,016 |
| deviations from the reference | 10 | 10 | 1 | 1 |

## The pinned programs

Totals per test module; a module counts from the step that adds it.

| module | programs | form | stage 5 | step 1 | step 2 | step 3 |
|---|---:|---|---:|---:|---:|---:|
| words | 80 | interpreted | 3,031,565 | 2,741,169 | 2,530,651 | 2,690,622 |
| | | compiled | 1,351,359 | 1,351,359 | 1,353,559 | 1,340,318 |
| modes | 8 | interpreted | 282,358 | 255,301 | 325,754 | 340,451 |
| | | compiled | 51,312 | 51,312 | 67,166 | 67,166 |
| combinators | 30 | interpreted | 3,952,544 | 3,575,393 | 4,717,281 | 4,586,181 |
| | | compiled | 1,507,387 | 1,507,387 | 1,984,022 | 1,879,176 |
| text | 43 | interpreted | 3,811,959 | 3,479,165 | 3,989,389 | 4,329,925 |
| | | compiled | 1,619,826 | 1,619,826 | 1,986,681 | 1,946,308 |
| types | 46 | interpreted | | | 2,586,877 | 2,722,155 |
| | | compiled | | | 1,062,089 | 1,058,415 |
| sets | 73 | interpreted | | | | 4,056,867 |
| | | compiled | | | | 1,525,141 |

Over the 161 programs stage 5 pinned:

| | stage 5 | step 1 | step 2 | step 3 |
|---|---:|---:|---:|---:|
| interpreted | 11,078,426 | 10,051,028 | 11,563,075 | 11,947,179 |
| against stage 5 | | −9.3% | +4.4% | +7.8% |
| median program, against stage 5 | | 0.89 | | 0.97 |
| compiled | 4,529,884 | 4,529,884 | 5,391,428 | 5,232,968 |
| against stage 5 | | 0.0% | +19.0% | +15.5% |

No pinned outcome changed at any step.

- *Step 1* cut every interpreted count, by 0.67 to 0.93 of stage 5's:
  `step` is smaller, and `dip` puts a symbol back with one `Lit`. The
  compiled form has no `word` and kept every count.
- *Step 2* pays for the checks. `succ` and `pred` must tell a truth value
  from an integer, so every program that counts down pays.
- *Step 3* adds 4–5% to every interpreted program, the price of a larger
  `step`. The compiled counts fall, since `not` is one kernel word and
  `times` counts down by the kernel's `<`.

## Single programs

| program | form | stage 5 | step 1 | step 2 | step 3 |
|---|---|---:|---:|---:|---:|
| `1 2 + dup +` | interpreted | 5,337 | 4,808 | 4,952 | 5,260 |
| | compiled | 668 | 668 | 668 | 668 |
| `5 succ` | interpreted | 3,097 | 2,772 | 9,372 | 9,883 |
| | compiled | 427 | 427 | 3,183 | 3,183 |
| `5 sumto` | interpreted | 154,288 | 140,114 | 184,099 | 192,269 |
| | compiled | 30,103 | 30,103 | 39,822 | 39,822 |
| `true not` | interpreted | 7,364 | 6,554 | 17,626 | 1,713 |
| | compiled | 2,264 | 2,264 | 7,524 | 116 |
| `2 [10] times` | interpreted | | | 173,598 | 99,463 |
| | compiled | | | 33,298 | 17,751 |
| `3 3 >=` | interpreted | | | 6,471 | 24,720 |
| `[dup] first [1] dip` | interpreted | 8,321 | 5,588 | 5,792 | 6,038 |
| | compiled | 642 | 642 | 642 | 642 |

Sets, at step 3, unfuelled:

| program | interpreted | compiled |
|---|---:|---:|
| `{1 2} {2 3} and first` | 39,239 | |
| `{1 2} {2 3} xor` | 54,026 | 10,318 |
| `{1 2 3} [2 <] filter`, the dearest pinned | 475,542 | 252,185 |
| the 73 pinned set programs, median | 4,704 | 1,415 |

Two designs were measured and dropped on the way:

- *A derived complement.* A derived loop costs about 300,000
  interpreted contractions per element, and `{1 2} not size` passed the
  reader's cap of 5,000,000. The kernel's `not` replaced it.
- *Unions by repeated insertion.* `{1 2} {2 3} and first` took 1,593,877
  contractions; merging the ascending members brings it to 39,239.

## Level 1

`1 2 + dup +` and `1 2 + sq` under SKIjack's interpreter `wfN`,
interpreted form, fuel 7,000; the answer to "is the top 6?":

| | stage 5 | step 1 | step 2 | step 3 |
|---|---:|---:|---:|---:|
| `1 2 + dup +` | 40,205,700 | 33,524,535 | 35,243,483 | 38,575,065 |
| `1 2 + sq` | 41,419,680 | 34,659,638 | 36,399,854 | 39,777,702 |

The compiled form's runs (2,328,665 and 2,337,648) did not change.

## Avon

Avon's SKIlark workloads, phase 2's eight programs in both forms,
fuelled and unfuelled, and phase 1's runs: 41 runs, copy mode
(Avon #68 at stage 5, #69 at step 3).

| | stage 5 | step 3 |
|---|---:|---:|
| the 41 runs | 742,609 | 882,928 |
| interpreted | 551,541 | 660,290 |
| compiled | 101,382 | 132,952 |
| phase 1 | 89,686 | 89,686 |
| absorbed by Avon's jets, all three dictionaries | 30.5% | 30.9% |
| SKIlark's `step` in the census of both corpora | 13.2%, 502 calls × 648 | 14.3%, 614 calls × 607 |

Without jets the 41 runs take under 10 ms on Avon, too little to time.

## CI

Wall time of each job on GitHub's runners. The same work varies by up to
half from one run to the next.

| PR | Avon | Python 3.10 | 3.11 | 3.12 | 3.13 |
|---|---:|---:|---:|---:|---:|
| #10, stage 5 | 1h58m | 58m | 1h03m | 37m | 37m |
| #11, step 1 | 1h22m | 1h33m | 1h01m | 52m | 1h04m |
| #12, step 2 | 3h03m | 2h18m | 1h09m | 1h43m | 1h40m |
| #13, step 3 | 2h24m | 1h41m | 1h24m | 2h13m | 1h09m |
| #15, a linear abstraction, xdist, Avon | 58m (reference) | 16m | 11m | 12m | 9m |
| #16, the reference in four shards | 9–15m (and slow, 3m) | 14m | 11m | 12m | 10m |
| #18, stage 7 and the numbers | 34–43m (and slow, 3m) | 23m | 16m | 15m | 15m |

Two changes cut CI from hours to a quarter of an hour:

- *A linear bracket abstraction* (#15). aviary_kernel's
  `bracket_abstract` asks `free_vars` of a body at every level it
  descends, and `free_vars` walks the body whole; a compiled set program
  spent 640 of its 644 s of compile there. `skilark.abstraction` answers
  each node once, for one compile, with aviary's terms hash for hash: that
  program compiles in 4.7 s, from 78.5, and the suite takes 9.5 minutes
  on aviary on four workers, from 70 serially.
- *Avon and sharding* (#15, #16). The Python jobs reduce on Avon (the
  suite in 2.5 minutes locally); the reference job checks every
  reduction against aviary in four shards (`SKILARK_SHARD`), and the slow
  tests run alone.
- *The reference on demand* (#20). The pinned outcomes and counts hold
  Avon to aviary's numbers in every job, so the reference runs on each
  push to master and on a pull request labelled `reference`. An unlabelled
  pull request waits for its slowest Python job, 15 to 24 minutes, not
  for the shards' 20 to 47.

## Numbers on skijack's operations

The kernel's naturals on skijack's `natAdd natSub natMul natIfEq natIfLe`,
the integer operations casing both integers first (PLAN.md §3). Avon,
share mode with templates and data jets, to normal form:

| program | before | after | native operations |
|---|---:|---:|---:|
| `200 200 *` | 8,360,924 | 160,092 | 1 |
| `200 200 * 7 /` | 8,607,178 | 131,564 | 11,430 |
| `200 200 * 7 /`, on `natDiv` | 131,564 | 22,986 | 2 |
| `200 200 * 7 rem`, on `natRem` | 108,716 | 138 | 2 |
| `200 200 * 199 <` | 84,363 | 136 | 3 |
| `200 200 * 199 200 * -` | 16,520,814 | 962 | 4 |
| `6 fact` | 13,548 | 5,980 | 30 |
| `30 sumto` | 17,805 | 15,750 | 149 |
| `[1 2 3] [dup *] map` | 6,409 | 5,913 | 12 |

Each operation cases on its numerals first: an operation fires natively
only on words, and without the cases `200 200 * 199 200 * -` took 398,959.
On aviary, which runs the operations as their terms: the 363 pinned
programs take 3.5% more interpreted contractions and 0.5% more compiled;
`step` was 57,842 atoms, from 45,016. Division then took skijack 0.2.2's
`natDiv` and `natRem` (skijack #25, Avon #70) in place of a loop of
native subtractions, the two rows marked: `step` is 57,570 atoms, and the
three pinned programs that divide take 0.2% to 0.4% fewer contractions.

## Room left

- *`word`:* 29 constructors of the 31 the cap allows (its one-field
  constructors take 30 arguments of 32), so two kernel words fit. A third
  needs Avon's `AV_JET_ARITY_MAX` and its template markers raised
  together (to 64 at most, the width of its marker sets) or `word` split
  in two.
- *`item`:* 7 constructors. Each case on an item gains a branch per
  kind, and `step` grew by a third with sets, so a new kind costs every
  interpreted word a few percent.
- *SKIjack's nesting:* programs past 240 levels spill into equations;
  the deepest pinned program nests 174.
- *CI:* the Python jobs take 15 to 23 minutes and the reference shards
  34 to 43, against GitHub's six-hour stop; a fifth shard is the next
  lever when the shards pass an hour.
