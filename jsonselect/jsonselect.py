#!/usr/bin/env python
'''pyjsonselect is a fully-compliant implementation of JSONSelect.

Usage:

    # prints 1, 2
    for v in jsonselect.match('.foo', {'foo': 1, 'bar': {'foo': 2}}):
        print v

If you care about the iteration order of your keys (e.g. if you're processing a
JSON file), then consider using collections.OrderedDict instead of the built-in
Python dict.

If you're not satisfied with pyjsonselect's performance, you may wish to prune
some subtrees out of the selector search. You may do this by passing a filter
function to match():

    # prints 1 (the 2 value is in a pruned subtree).
    obj = {'foo': 1, 'bar': {'foo': 2}}
    filter_fn = lambda obj, matches: obj == {'foo': 2}
    for v in jsonselect.match('.foo', obj, bailout_fn=filter_fn):
        print v

For large objects, suitable pruning can result in a massive speedup.

Aside from bailout_fn, this is a direct port of the jsonselect.js reference
implementation.
'''

import json
import re
import sys

PY3 = sys.version_info[0] == 3


if PY3:
    stringtype=str
    
    def iteritems(d):
        return d.items()
        
    def iterkeys(d):
        return d.keys()
else:
    stringtype=basestring

    def iteritems(d):
        return d.iteritems()
    def iterkeys(d):
        return d.iterkeys()


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
    "snex": "string or number expected",
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
    num=6  # numbers


# The primary lexing regular expression in jsonselect
pat = re.compile(
    "^(?:" +
    # (1) whitespace
    "([\\r\\n\\t\\ ]+)|" +
    # (2) one-char ops
    "([!~*,>\\)\\(])|" +
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
    "\\.((?:[_a-zA-Z]|[^" + u'\u0000-\u007f' + "]|\\\\[^\\r\\n\\f0-9a-fA-F])(?:[\\$_a-zA-Z0-9\\-]|[^" + u'\u0000-\u007f' + "]|(?:\\\\[^\\r\\n\\f0-9a-fA-F]))*)|" +
    # (10) numbers
    "(-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)"
    ")"
)


def _reExec(regex, string):
    '''This returns [full match, group1, group2, ...], just like JS.'''
    m = regex.search(string)
    if not m: return None
    return [m.group()] + list(m.groups())


def _jsTypeof(o):
    '''Return a string similar to JS's typeof.'''
    if o == None:
        return 'object'
    elif o == Undefined:
        return 'undefined'
    elif isinstance(o, bool):
        return 'boolean'
    if isinstance(o, int) or isinstance(o, float):
        return 'number'
    elif isinstance(o, list) or isinstance(o, dict):
        return 'object'
    elif isinstance(o, stringtype):
        return 'string'
    raise ValueError('Unknown type for object %s (%s)' % (o, type(o)))


# A regular expression for matching "nth expressions" (see grammar, what :nth-child() eats)
nthPat = re.compile(r'^\s*\(\s*(?:([+\-]?)([0-9]*)n\s*(?:([+\-])\s*([0-9]))?|(odd|even)|([+\-]?[0-9]+))\s*\)')
def lex(string, off=None):
    if not off: off = 0
    m = _reExec(pat, string[off:])
    if not m: return None
    off+=len(m[0])
    a = None
    if m[1]: a = [off, " "]
    elif m[2]: a = [off, m[0]]
    elif m[3]: a = [off, toks.typ, m[0]]
    elif m[4]: a = [off, toks.psc, m[0]]
    elif m[5]: a = [off, toks.psf, m[0]]
    elif m[6]: te("upc", string)
    elif m[8]: a = [off, toks.ide if m[7] else toks.str, jsonParse(m[8])]
    elif m[9]: te("ujs", string)
    elif m[10]: a = [off, toks.ide, re.sub(r'\\([^\r\n\f0-9a-fA-F])', r'\1', m[10])]
    elif m[11]: a = [off, toks.num, jsonParse(m[11])]
    return a


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

def ist(o, t):
    return _jsTypeof(o) == t


def num_wrap(op):
    def wrap(lhs, rhs):
        try:
            return op(lhs, rhs)
        except TypeError:
            return float('nan')
    return wrap

operators = {
    '*':  [ 9, num_wrap(lambda lhs, rhs: lhs * rhs) ],
    '/':  [ 9, num_wrap(lambda lhs, rhs: lhs / rhs) ],
    '%':  [ 9, num_wrap(lambda lhs, rhs: lhs % rhs) ],
    '+':  [ 7, num_wrap(lambda lhs, rhs: lhs + rhs) ],
    '-':  [ 7, num_wrap(lambda lhs, rhs: lhs - rhs) ],
    '<=': [ 5, lambda lhs, rhs: ist(lhs, 'number') and ist(rhs, 'number') and lhs <= rhs or ist(lhs, 'string') and ist(rhs, 'string') and lhs <= rhs ],
    '>=': [ 5, lambda lhs, rhs: ist(lhs, 'number') and ist(rhs, 'number') and lhs >= rhs or ist(lhs, 'string') and ist(rhs, 'string') and lhs >= rhs ],
    '$=': [ 5, lambda lhs, rhs: ist(lhs, 'string') and ist(rhs, 'string') and lhs.rfind(rhs) == len(lhs) - len(rhs) ],
    '^=': [ 5, lambda lhs, rhs: ist(lhs, 'string') and ist(rhs, 'string') and lhs.find(rhs) == 0 ],
    '*=': [ 5, lambda lhs, rhs: ist(lhs, 'string') and ist(rhs, 'string') and lhs.find(rhs) != -1 ],
    '>':  [ 5, lambda lhs, rhs: ist(lhs, 'number') and ist(rhs, 'number') and lhs > rhs or ist(lhs, 'string') and ist(rhs, 'string') and lhs > rhs ],
    '<':  [ 5, lambda lhs, rhs: ist(lhs, 'number') and ist(rhs, 'number') and lhs < rhs or ist(lhs, 'string') and ist(rhs, 'string') and lhs < rhs ],
    '=':  [ 3, lambda lhs, rhs: lhs == rhs ],
    '!=': [ 3, lambda lhs, rhs: lhs != rhs ],
    '&&': [ 2, lambda lhs, rhs: lhs and rhs ],
    '||': [ 1, lambda lhs, rhs: lhs or rhs ]
}


# TODO(danvk): is this the canonical way to create a unique symbol?
class Undefined(object):
    pass


def exprLex(string, off):
    m = _reExec(exprPat, string[off:])
    v = None
    if m:
        off += len(m[0])
        v = m[1] or m[2] or m[3] or m[5] or m[6]
        if m[1] or m[2] or m[3]:
            return [off, 0, jsonParse(v)]
        elif m[4]:
            return [off, 0, Undefined]
        return [off, v]


def exprParse2(string, off):
    if (not off): off = 0
    # first we expect a value or a '('
    l = exprLex(string, off)
    lhs = Undefined
    if l and l[1] == '(':
        lhs = exprParse2(string, l[0])
        p = exprLex(string, lhs[0])
        if not p or p[1] != ')': te('epex', string)
        off = p[0]
        lhs = [ '(', lhs[1] ]
    elif not l or (l[1] and l[1] != 'x'):
        te("ee", string + " - " + ( l[1] and l[1] ))
    else:
        lhs = Undefined if (l[1] == 'x') else l[2]
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
    if _jsTypeof(rhs) != 'object' or rhs[0] == '(' or operators[op[1]][0] < operators[rhs[1]][0]:
        v = [lhs, op[1], rhs]
    else:
        v = rhs
        while _jsTypeof(rhs[0]) == 'object' and rhs[0][0] != '(' and operators[op[1]][0] >= operators[rhs[0][1]][0]:
            rhs = rhs[0]
        rhs[0] = [lhs, op[1], rhs[0]]
    return [off, v]


def exprParse(string, off):
    def deparen(v):
        if _jsTypeof(v) != 'object' or v == None:
            return v
        elif v[0] == '(':
            return deparen(v[1])
        else:
            return [deparen(v[0]), v[1], deparen(v[2])]
    e = exprParse2(string, off or 0)
    return [e[0], deparen(e[1])]


def exprEval(expr, x):
    if expr == Undefined:
        return x
    if expr == None or _jsTypeof(expr) != 'object':
        return expr
    lhs = exprEval(expr[0], x)
    rhs = exprEval(expr[2], x)
    return operators[expr[1]][1](lhs, rhs)


# THE PARSER

def parse(string, off=0, nested=None, hints=None):
    if not hints: hints = {}
    if not nested: hints = {}

    a = []
    am = None
    readParen = None
    if not off: off = 0

    while True:
        s = parse_selector(string, off, hints)
        a.append(s[1])
        off = s[0]
        s = lex(string, off)
        if s and s[1] == " ":
            off = s[0]
            s = lex(string, off)
        if not s:
            break
        # now we've parsed a selector, and have something else...
        if s[1] == ">" or s[1] == "~":
            if s[1] == "~":
                hints['usesSiblingOp'] = True
            a.append(s[1])
            off = s[0]
        elif s[1] == ",":
            if am == None:
                am = [ ",", a ]
            else:
                am.append(a)
            a = []
            off = s[0]
        elif s[1] == ")":
            if not nested:
                te("ucp", s[1])
            readParen = 1
            off = s[0]
            break

    if nested and not readParen:
        te("mcp", string)
    if am:
        am.append(a)
    rv = None
    if not nested and (hints.get('usesSiblingOp') or hints.get('usesSubject')):
        rv = normalize(am or a);
    else:
        rv = am or a
    return [off, rv]


def normalizeOne(sel):
    sels = []
    s = None
    for i in range(len(sel)):
        if sel[i] == '~':
            # `A ~ B` maps to `:has(:root > A) > B`
            # `Z A ~ B` maps to `Z :has(:root > A) > B, Z:has(:root > A) > B`
            # This first clause, takes care of the first case, and the first half of the latter case.
            if i < 2 or sel[i-2] != '>':
                s = sel[:i-1]
                s = s + [{'has':[[{'pc': ":root"}, ">", sel[i-1]]]}, ">"]
                s = s + sel[i+1:]
                sels.append(s);
            # here we take care of the second half of above:
            # (`Z A ~ B` maps to `Z :has(:root > A) > B, Z :has(:root > A) > B`)
            # and a new case:
            # Z > A ~ B maps to Z:has(:root > A) > B
            if i > 1:
                at = i - 3 if sel[i-2] == '>' else i-2
                s = sel[:at]
                z = {}
                for k in iterkeys(sel[at]):
                    if k in sel[at]:
                        z[k] = sel[at][k]
                if not z.get('has'):
                    z['has'] = []
                z['has'].append([{'pc': ":root"}, ">", sel[i-1]])
                s = s + [z, '>'] + sel[i+1:]
                sels.append(s)
            break

    for i in range(len(sel)):
        if _jsTypeof(sel[i]) == 'object' and sel[i].get('subject'):
            # Map `foo !bar baz` to `foo bar:has(baz)`
            s = sel[:i] + [sel[i+1]]
            s[-1].update({
                'has': [sel[i+2:]]
            })
            sels.append(s)
            break

    if i == len(sel):
        return sel
    if len(sels) > 1:
        return [','] + sels
    else:
        return sels[0]


def normalize(sels):
    if sels[0] == ',':
        r = [","]
        for i in range(1, len(sels)):
            s = normalizeOne(s[i])
            r = r + (s[1:] if s[0] == ',' else s)
        return r
    else:
        return normalizeOne(sels)


def parse_selector(string, off, hints):
    soff = off
    s = { }
    l = lex(string, off)
    # skip space
    if l and l[1] == " ":
        soff = off = l[0]
        l = lex(string, off)
    if l and l[1] == toks.typ:
        s['type'] = l[2]
        off = l[0]
        l = lex(string, off)
    elif l and l[1] == "*":
        # don't bother representing the universal sel, '*' in the
        # parse tree, cause it's the default
        off = l[0]
        l = lex(string, off)
    elif l and l[1] == "!":
        off = l[0]
        s['subject'] = True
        hints['usesSubject'] = True

    # now support either an id or a pc
    while True:
        if l == None:
            break
        elif l[1] == toks.ide:
            if s.get('id'): te("nmi", l[1])
            s['id'] = l[2]
        elif l[1] == toks.psc:
            if s.get('pc') or s.get('pf'):
                te("mpc", l[1])
            # collapse first-child and last-child into nth-child expressions
            if l[2] == ":first-child":
                s['pf'] = ":nth-child"
                s['a'] = 0
                s['b'] = 1
            elif l[2] == ":last-child":
                s['pf'] = ":nth-last-child"
                s['a'] = 0
                s['b'] = 1
            else:
                s['pc'] = l[2]
        elif l[1] == toks.psf:
            if l[2] == ":val" or l[2] == ":contains":
                s['expr'] = [ Undefined, '=' if l[2] == ":val" else "*=", Undefined]
                # any amount of whitespace, followed by paren, string, paren
                off = l[0]
                l = lex(string, off)
                if l and l[1] == " ":
                    off = l[0]
                    l = lex(string, off)
                if not l or l[1] != "(":
                    te("pex", string)
                off = l[0]
                l = lex(string, off)
                if l and l[1] == " ":
                    off = l[0]
                    l = lex(string, off)
                if not l or (l[1] != toks.str and l[1] != toks.num):
                    te("snex", string)
                s['expr'][2] = l[2]
                off = l[0]
                l = lex(string, off)
                if l and l[1] == " ":
                    off = l[0]
                    l = lex(string, off)
                if not l or l[1] != ")":
                    te("epex", string)
            elif l[2] == ":has":
                # any amount of whitespace, followed by paren
                off = l[0]
                l = lex(string, off)
                if l and l[1] == " ":
                    off = l[0]
                    l = lex(string, off)
                if not l or l[1] != "(":
                    te("pex", string)
                h = parse(string, l[0], True)
                l[0] = h[0]
                if not s.get('has'): s['has'] = []
                s['has'].append(h[1])
            elif l[2] == ":expr":
                if s.get('expr'):
                    te("mexp", string)
                e = exprParse(string, l[0])
                l[0] = e[0]
                s['expr'] = e[1]
            else:
                if s.get('pc') or s.get('pf'):
                    te("mpc", string)
                s['pf'] = l[2];
                m = _reExec(nthPat, string[l[0]:])
                if not m:
                    te("mepf", string)
                if m[5]:
                    s['a'] = 2
                    s['b'] = 1 if m[5] == "odd" else 0
                elif m[6]:
                    s['a'] = 0
                    s['b'] = int(m[6])
                else:
                    s['a'] = int((m[1] or "+") + (m[2] or "1"))
                    s['b'] = int(m[3] + m[4]) if m[3] else 0
                l[0] += len(m[0])
        else:
            break
        off = l[0]
        l = lex(string, off)

    # now if we didn't actually parse anything it's an error
    if soff == off:
        te("se", string)

    return [off, s]


# THE EVALUATOR

def isArray(o):
    return isinstance(o, list)

# TODO(danvk): this works around a deficiency of JS that Python doesn't share.
def mytypeof(o):
    if o == None:
        return "null"
    to = _jsTypeof(o)
    if to == "object" and isArray(o):
        to = "array"
    return to


# mn = "match node"?
def mn(node, sel, Id, num, tot):
    sels = []
    cs = sel[1] if sel[0] == '>' else sel[0]
    m = True
    mod = None
    if cs.get('type'):
        m = m and (cs['type'] == mytypeof(node))
    if cs.get('id'):
        m = m and (cs['id'] == Id)
    if m and cs.get('pf'):
        if cs['pf'] == ":nth-last-child":
            if num == None or tot == None:
                num = float('nan')  # mirror JS quirk
            else:
                num = tot - num
        else:
            if num != None:
                num+=1
            else:
                num = float('nan')  # mirror a JS quirk which jsonselect uses
        if cs.get('a') == 0:
            m = cs.get('b') == num
        else:
            mod = (num - cs['b']) % cs['a']

            m = not mod and ((num*cs['a'] + cs['b']) >= 0)
    if m and cs.get('has'):
        for el in cs['has']:
            try:
                next(_forEach(el, node))
                continue
            except StopIteration:
                pass
            m = False
            break
    if m and cs.get('expr'):
        m = exprEval(cs['expr'], node)

    # should we repeat this selector for descendants?
    if sel[0] != ">" and sel[0].get('pc') != ":root":
        sels.append(sel)

    if m:
        # is there a fragment that we should pass down?
        if sel[0] == ">":
            if len(sel) > 2:
                m = False
                sels.append(sel[2:])
        elif len(sel) > 1:
            m = False
            sels.append(sel[1:])

    return [m, sels]


def _forEach(sel, obj, Id=None, num=None, tot=None, bailout_fn=None):
    a = sel[1:] if (sel[0] == ",") else [sel]
    a0 = []
    call = False
    i = 0
    j = 0
    k = None
    x = None
    for i in range(len(a)):
        x = mn(obj, a[i], Id, num, tot)
        if x[0]:
            call = True
        for v in x[1]:
            a0.append(v)

    skip_recursion = False
    if bailout_fn:
        if bailout_fn(obj, call):
            skip_recursion = True

    if not skip_recursion:
        if len(a0) and _jsTypeof(obj) == "object":
            if len(a0) >= 1:
                a0 = [','] + a0
            if isArray(obj):
                for i, v in enumerate(obj):
                    iterator = _forEach(a0, v, num=i, tot=len(obj), bailout_fn=bailout_fn)
                    for o in iterator:
                        yield o
            else:
                if obj:
                    for k, v in iteritems(obj):
                        iterator = _forEach(a0, v, Id=k, bailout_fn=bailout_fn)
                        for o in iterator:
                            yield o

    if call:
        yield obj


def interpolate(sel, arr):
    while '?' in sel:
        s = arr[0]
        if isinstance(s, stringtype):
            s = json.dumps(s)
        sel = sel.sub(r'\?', s, sel)
        arr = arr[1:]
    if arr:
        raise ValueError("too many parameters supplied")
    return sel


def match(sel, obj, arr=None, bailout_fn=None):
    '''Match a selector to an object, yielding the matched values.

    Args:
        sel: The JSONSelect selector to apply (a string)
        obj: The object against which to apply the selector
        arr: If sel contains ? characters, then the values in this array will
             be safely interpolated into the selector.
        bailout_fn: A callback which takes two parameters, |obj| and |matches|.
             This will be called on every node in obj. If it returns True, the
             search for matches will be aborted below that node. The |matches|
             parameter indicates whether the node matched the selector. This is
             intended to be used as a performance optimization.
    '''
    if arr:
        sel = interpolate(sel, arr)
    sel = parse(sel)[1]
    return _forEach(sel, obj, bailout_fn=bailout_fn)
