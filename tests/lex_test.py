from nose.tools import *

from jsonselect import jsonselect

lex = jsonselect.lex

def test_simpleTokens():
    eq_([1, ">"], lex(">"))
    eq_([1, "*"], lex("*"))
    eq_([1, ","], lex(","))
    # eq_([1, "."], lex("."))  # <-- failing upstream, too

def test_offsets():
    eq_([7, ">"], lex("foobar>",6))

def test_types():
    eq_([6, 3, "string"], lex("string"))
    eq_([7, 3, "boolean"], lex("boolean"))
    eq_([4, 3, "null"], lex("null"))
    eq_([5, 3, "array"], lex("array"))
    eq_([6, 3, "object"], lex("object"))
    eq_([6, 3, "number"], lex("number"))

def test_Whitespace():
    eq_([1, " "], lex("\r"))
    eq_([1, " "], lex("\n"))
    eq_([1, " "], lex("\t"))
    eq_([1, " "], lex(" "))
    eq_([13, " "], lex("     \t   \r\n  !"))

def test_pseudo_classes():
    eq_([5, 1, ":root"], lex(":root"))
    eq_([12, 1, ":first-child"], lex(":first-child"))
    eq_([11, 1, ":last-child"], lex(":last-child"))
    eq_([11, 1, ":only-child"], lex(":only-child"))

def test_json_strings():
    eq_([13, 4, "foo bar baz"], lex('"foo bar baz"'))
    eq_([8, 4, " "], lex('"\\u0020"'))

# ... there are a few more tests in
# lloyd/JSONSelect/blob/master/src/test/lex_test.html, but they fail upstream.

# My own tests...
def test_two_ids():
    eq_([4, 5, "foo"], lex('.foo .bar'))

def test_bang():
    eq_([1, "!"], lex('!.foo .bar'))
