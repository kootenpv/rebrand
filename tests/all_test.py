import time
import os
import shutil
from rebrand import ts_replacer, run


def simple(a, b, c, d):
    ts = ts_replacer(a, b)
    assert ts.replace(c) == d


def test_two_input():
    simple("one two", "nostalgia", "one-two", "nostalgia")


def test_two_output():
    simple("nostalgia", "one two", "Nostalgia", "OneTwo")


def test_camelcase():
    simple("SomeThing", "AnotherThing", "some-thing", "another-thing")


def test_one():
    simple("oNe", "ancient", "one", "ancient")
    simple("one", "ancient", "ONE", "ANCIENT")


def test_run():
    a, b = "oldPackage", "newPackage"
    dirname = "/tmp/rebrand_{}_{}".format(a, time.time())
    try:
        os.mkdir(dirname)
        with open(os.path.join(dirname, a), "w") as f:
            f.write(a)
        run(a, b, dirname)
    finally:
        shutil.rmtree(dirname)
        shutil.rmtree(dirname.replace(a, b))
