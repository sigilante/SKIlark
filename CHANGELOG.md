# Changelog

## Unreleased (0.11.0)

- **The reference's own tests** (stage 16, `tests/test_joytest2.py`):
  Wodan58/Joy's `test2/` copied whole at fe9fa0f with its licence
  (`tests/joy/`). Every file is run by the model and, on the slow job, by
  SKIlark, and every known failure is pinned with its reason
  (`PLAN.md` §3, stage 16).

## 0.10.0 (2026-11-07)

Joy in full, stages 7 to 15 (`PLAN.md` §3), each pinned by its tests:

- **The library words** (stage 7, `tests/test_library.py`): the stack
  words, the n-ary combinators, the type conditionals, `cond case
  opcase`, `split some all`, and the tree combinators.
- **The kernel's further words in `ext`** (stage 8): `size at compare
  name body intern strtol format` and the I/O words, in a sum of their
  own, so `word` stays at 30 of the 31 constructors Avon's cap of 32
  arguments allows.
- **The pure words left** (stage 9, `tests/test_pure.py`): `div pick
  condlinrec condnestrec casting`, `compare` a kernel word.
- **Symbols and their names** (stage 10, `tests/test_symbols.py`): `name
  body intern`, `intern` in the interpreted form alone.
- **Numbers to and from text** (stage 11, `tests/test_numtext.py`):
  `strtol format`.
- **Joy files and examples** (stage 12, `tests/test_examples.py`,
  `examples/`).
- **The SKI underneath** (stage 13, `tests/test_ski.py`): `--ski` prints
  a program's term, and `--ski-out` writes it for Avon.
- **I/O** (stage 14, `tests/test_io.py`): `put putch putchars get argc
  argv getenv clock abort quit`, which stop the run for the host to
  answer (`skilark/io.py`).
- **I/O through drivers** (stage 15, `skilark/door.py`): the I/O words
  answered by SKIjack's reference drivers or by `avon run --kernel`.

The compiled form refuses the I/O words and `intern`, which need the
interpreted form's datum (`PLAN.md` §3, stages 10 and 14).

Requires skijack 0.2.6.  Avon is optional for users; CI pins it at
`sigilante/avon` master `a4b2db4` and runs the suite on it.

Known deviations from the reference implementation, pinned with their
reason: `genrec`'s R2 and `treerec`'s and `treegenrec`'s C see a
quotation, not the reference's own word; and after an error SKIlark runs
on the stack the erring term began with, where the reference keeps the
stack as the error left it (stage 14).  The file words are decided for
later (`PLAN.md` §3, stage 15).

## 0.9.0 (2026-10-24)

Never tagged or published.  The version number was set during stage 6
and stayed at 0.9.0 while stages 7 to 15 were built; those are listed
under 0.10.0.  At 0.9.0: phases 1–3, predicates in zero knowledge, and Joy in full through stage
6: signed integers, truth values, quotations as lists, the stack as
data, the recursion combinators, characters, strings and sets, `typeof`
and the type tests.
