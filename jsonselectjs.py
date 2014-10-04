#!/usr/bin/env python
'''Direct port of jsonselect.js using JSONPath.'''

import json
import re


def jsonParse(string):
    return json.loads(string)


# emitted error codes.
errorCodes = {
    "bop":  "binary operator expected",
    "ee":   "expression expected",
    "epex": "closing paren expected ')'",
    "ijs":  "invalid json string",
    "mcp":  "missing closing paren",
    "mepf": "malformed expression in pseudo-function",
    "mexp": "multiple expressions not allowed",
    "mpc":  "multiple pseudo classes (:xxx) not allowed",
    "nmi":  "multiple ids not allowed",
    "pex":  "opening paren expected '('",
    "se":   "selector expected",
    "sex":  "string expected",
    "sra":  "string required after '.'",
    "uc":   "unrecognized char",
    "ucp":  "unexpected closing paren",
    "ujs":  "unclosed json string",
    "upc":  "unrecognized pseudo class"
}


class JsonSelectError(Exception):
    pass


# throw an error message
def te(ec, context):
    raise JsonSelectError(errorCodes[ec] + ( context and " in '" + context + "'"))


# THE LEXER
class toks(object):
    psc=1  # pseudo class
    psf=2  # pseudo class function
    typ=3  # type
    str=4  # string
    ide=5  # identifiers (or "classes", stuff after a dot)


# The primary lexing regular expression in jsonselect
pat = re.compile(
    "^(?:" +
    # (1) whitespace
    "([\\r\\n\\t\\ ]+)|" +
    # (2) one-char ops
    "([~*,>\\)\\(])|" +
    # (3) types names
    "(string|boolean|null|array|object|number)|" +
    # (4) pseudo classes
    "(:(?:root|first-child|last-child|only-child))|" +
    # (5) pseudo functions
    "(:(?:nth-child|nth-last-child|has|expr|val|contains))|" +
    # (6) bogusly named pseudo something or others
    "(:\\w+)|" +
    # (7 & 8) identifiers and JSON strings
    "(?:(\\.)?(\\\"(?:[^\\\\\\\"]|\\\\[^\\\"])*\\\"))|" +
    # (8) bogus JSON strings missing a trailing quote
    "(\\\")|" +
    # (9) identifiers (unquoted)
    "\\.((?:[_a-zA-Z]|[^\\0-\\0177]|\\\\[^\\r\\n\\f0-9a-fA-F])(?:[\\$_a-zA-Z0-9\\-]|[^\\u0000-\\u0177]|(?:\\\\[^\\r\\n\\f0-9a-fA-F]))*)" +
    ")"
)


# A regular expression for matching "nth expressions" (see grammar, what :nth-child() eats)
nthPat = re.compile(r'^\s*\(\s*(?:([+\-]?)([0-9]*)n\s*(?:([+\-])\s*([0-9]))?|(odd|even)|([+\-]?[0-9]+))\s*\)')
def lex(string, off):
    if (!off) off = 0;
    m = pat.search(string[off:])
    if (!m) return None
    m = [m.group()] + m.groups()
    off+=len(m[0])
    a = None;
    if (m[1]) a = [off, " "];
    else if (m[2]) a = [off, m[0]];
    else if (m[3]) a = [off, toks.typ, m[0]];
    else if (m[4]) a = [off, toks.psc, m[0]];
    else if (m[5]) a = [off, toks.psf, m[0]];
    else if (m[6]) te("upc", string);
    else if (m[8]) a = [off, m[7] ? toks.ide : toks.str, jsonParse(m[8])];
    else if (m[9]) te("ujs", string);
    else if (m[10]) a = [off, toks.ide, m[10].replace(/\\([^\r\n\f0-9a-fA-F])/g,"$1")];
    return a;


# THE EXPRESSION SUBSYSTEM

exprPat = re.compile(
        # skip and don't capture leading whitespace
        "^\\s*(?:" +
        # (1) simple vals
        "(true|false|null)|" +
        # (2) numbers
        "(-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)|" +
        # (3) strings
        "(\"(?:[^\\]|\\[^\"])*\")|" +
        # (4) the 'x' value placeholder
        "(x)|" +
        # (5) binops
        "(&&|\\|\\||[\\$\\^<>!\\*]=|[=+\\-*/%<>])|" +
        # (6) parens
        "([\\(\\)])" +
        ")"
)

# TODO(danvk): t is either 'number' or 'string'. make this work.
def is(o, t):
    return type(o) == type(t)

# TODO(danvk): fix .length, .indexOf, .lastIndexOf
operators = {
    '*':  [ 9, lambda lhs, rhs: lhs * rhs ],
    '/':  [ 9, lambda lhs, rhs: lhs / rhs ],
    '%':  [ 9, lambda lhs, rhs: lhs % rhs ],
    '+':  [ 7, lambda lhs, rhs: lhs + rhs ],
    '-':  [ 7, lambda lhs, rhs: lhs - rhs ],
    '<=': [ 5, lambda lhs, rhs: is(lhs, 'number') and is(rhs, 'number') and lhs <= rhs or is(lhs, 'string') and is(rhs, 'string') and lhs <= rhs ],
    '>=': [ 5, lambda lhs, rhs: is(lhs, 'number') and is(rhs, 'number') and lhs >= rhs or is(lhs, 'string') and is(rhs, 'string') and lhs >= rhs ],
    '$=': [ 5, lambda lhs, rhs: is(lhs, 'string') and is(rhs, 'string') and lhs.lastIndexOf(rhs) == lhs.length - rhs.length ],
    '^=': [ 5, lambda lhs, rhs: is(lhs, 'string') and is(rhs, 'string') and lhs.indexOf(rhs) == 0 ],
    '*=': [ 5, lambda lhs, rhs: is(lhs, 'string') and is(rhs, 'string') and lhs.indexOf(rhs) != -1 ],
    '>':  [ 5, lambda lhs, rhs: is(lhs, 'number') and is(rhs, 'number') and lhs > rhs or is(lhs, 'string') and is(rhs, 'string') and lhs > rhs ],
    '<':  [ 5, lambda lhs, rhs: is(lhs, 'number') and is(rhs, 'number') and lhs < rhs or is(lhs, 'string') and is(rhs, 'string') and lhs < rhs ],
    '=':  [ 3, lambda lhs, rhs: lhs == rhs ],
    '!=': [ 3, lambda lhs, rhs: lhs != rhs ],
    '&&': [ 2, lambda lhs, rhs: lhs and rhs ],
    '||': [ 1, lambda lhs, rhs: lhs or rhs ]
}

# TODO(danvk): Make a function which returns a list like JS's re.exec()
def exprLex(string, off):
    m = exprPat.exec(string[off:]);
    v = None
    if m:
        off += len(m[0])
        v = m[1] or m[2] or m[3] or m[5] or m[6]
        if m[1] or m[2] or m[3]:
            return [off, 0, jsonParse(v)]
        elif m[4]:
            return [off, 0, None]
        return [off, v]


def exprParse2(string, off):
    if (!off) off = 0;
    # first we expect a value or a '('
    l = exprLex(string, off)
    lhs = None
    if l and l[1] == '(':
        lhs = exprParse2(string, l[0])
        var p = exprLex(string, lhs[0])
        if !p or p[1] != ')': te('epex', string)
        off = p[0]
        lhs = [ '(', lhs[1] ]
    elif !l or (l[1] and l[1] != 'x'):
        te("ee", string + " - " + ( l[1] and l[1] ))
    else:
        lhs = None if (l[1] == 'x') else l[2])
        off = l[0]

    # now we expect a binary operator or a ')'
    op = exprLex(string, off)
    if not op or op[1] == ')':
        return [off, lhs]
    elif op[1] == 'x' or not op[1]:
        te('bop', string + " - " + ( op[1] and op[1] ))

    # tail recursion to fetch the rhs expression
    rhs = exprParse2(string, op[0])
    off = rhs[0]
    rhs = rhs[1]

    # and now precedence!  how shall we put everything together?
    v = None
    # TODO(danvk): typeof rhs == 'object' means it's a list or a dict
    if typeof rhs !== 'object' or rhs[0] == '(' or operators[op[1]][0] < operators[rhs[1]][0]:
        v = [lhs, op[1], rhs]
    else:
        v = rhs
        while typeof rhs[0] == 'object' and rhs[0][0] != '(' and operators[op[1]][0] >= operators[rhs[0][1]][0]:
            rhs = rhs[0]
        rhs[0] = [lhs, op[1], rhs[0]]
    return [off, v]


def exprParse(string, off):
    def deparen(v):
        # TODO(danvk): typeof rhs == 'object' means it's a list or a dict
        if typeof v !== 'object' or v == None:
            return v
        elif v[0] == '(':
            return deparen(v[1])
        else:
            return [deparen(v[0]), v[1], deparen(v[2])]
    e = exprParse2(string, off or 0)
    return [e[0], deparen(e[1])]


def exprEval(expr, x):
    # TODO(danvk): figure out why this would be undefined
    if expr == 'undefined':
        return x
    # TODO(danvk): typeof rhs == 'object' means it's a list or a dict
    elif expr == None or typeof expr !== 'object':
        return expr
    lhs = exprEval(expr[0], x)
    rhs = exprEval(expr[2], x)
    return operators[expr[1]][1](lhs, rhs)
