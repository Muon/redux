from nose.tools import eq_
from redux.ast import (Block, Assignment, WhileStmt, IfStmt, FunctionCall,
                       BreakStmt, ReturnStmt, CodeLiteral, BitfieldDefinition,
                       FunctionDefinition, Constant, VarRef, AddOp, EqualToOp,
                       GreaterThanOp, LogicalNotOp)
from redux.parser import parse


def test_valid_parses():
    valid_parses = [
        ("a = 1", Block([Assignment(VarRef("a"), Constant(1))])),
        ("a = \"abc\"", Block([Assignment(VarRef("a"), Constant("abc"))])),
        ("a = a + b", Block([Assignment(VarRef("a"), AddOp(VarRef("a"), VarRef("b")))])),
        ("a = f()", Block([Assignment(VarRef("a"), FunctionCall("f", []))])),
        ("a = f(1, 2)", Block([Assignment(VarRef("a"), FunctionCall("f", [Constant(1), Constant(2)]))])),
        ("if a == 0 end", Block([IfStmt(EqualToOp(VarRef("a"), Constant(0)), Block([]))])),
        ("if a == 0 else end", Block([IfStmt(EqualToOp(VarRef("a"), Constant(0)), Block([]), Block([]))])),
        ("if a == 0 elif b == 0 else end", Block([IfStmt(EqualToOp(VarRef('a'), Constant(0)), Block([]), Block([IfStmt(EqualToOp(VarRef('b'), Constant(0)), Block([]), Block([]))]))])),
        ("`PERFORM RAND;`", Block([CodeLiteral("PERFORM RAND;")])),
        ("while a > 0 end", Block([WhileStmt(GreaterThanOp(VarRef("a"), Constant(0)), Block([]))])),
        ("break", Block([BreakStmt()])),
        ("def f() return 1 end", Block([FunctionDefinition("f", [], Block([ReturnStmt(Constant(1))]))])),
        ("def f(a, b) end", Block([FunctionDefinition("f", ["a", "b"], Block([]))])),
        ("a = (b)", Block([Assignment(VarRef("a"), VarRef("b"))])),
        ("bitfield A x : 8 y : 8 end", Block([BitfieldDefinition("A", [("x", 8), ("y", 8)])])),
        ("a = not a", Block([Assignment(VarRef("a"), LogicalNotOp(VarRef("a")))])),
    ]

    for code, ast_ in valid_parses:
        yield check_valid_parse, code, ast_


def check_valid_parse(code, ast_):
    compiled_ast, errors = parse(code)
    assert not errors
    eq_(compiled_ast, ast_)