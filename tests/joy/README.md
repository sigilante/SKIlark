# Wodan58/Joy test2

`test2/` is the reference's own test suite: its 225 `.joy` files, copied
unchanged from [Wodan58/Joy](https://github.com/Wodan58/Joy) at
fe9fa0fa7db714340dbe17aedaff77f926e7c78a, the commit `joyref` models,
without its `CMakeLists.txt`. It has one file per builtin, and every line
of a file is a term the reference prints as `true`. `LICENSE` is the
reference's licence, which covers these files. Its notice must stay with
them.

`tests/test_joytest2.py` runs every file through the model and through
SKIlark. It also records why a file or term does not run.
