import pytest
from rebrand import get_scanner, replace


def simple(a, b, c, d):
    s = get_scanner(a, b, True, False)
    assert replace(s, c) == d


def test_two_input():
    simple("one two", "nostalgia", "one-two", "nostalgia")


def test_two_output():
    simple("nostalgia", "one two", "Nostalgia", "OneTwo")


def test_three_output():
    simple("one two", "ibm", "ONE_TWO", "IBM")


def test_two():
    simple("IBM", "ancient", "ibm", "ancient")
    simple("IBM", "ancient", "IBM", "ANCIENT")
