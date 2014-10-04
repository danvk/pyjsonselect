from nose.tools import *

import jsonselectjs

def test_simpleTokens():
    lex = jsonselectjs.lex
    eq_([1, ">"], lex(">"))
    eq_([1, "*"], lex("*"))
    eq_([1, ","], lex(","))
    eq_([1, "."], lex("."))
