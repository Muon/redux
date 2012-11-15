import sys
from collections import namedtuple
from redux.ast import Constant, BitfieldDefinition
from redux.callinliner import CallInliner
from redux.intrinsics import SayFunction, SqrtFunction
from redux.parser import parse
from redux.stringinliner import StringInliner
from redux.typeannotate import TypeAnnotator
from redux.types import str_, float_, int_, object_, is_numeric
from redux.visitor import ASTVisitor


ScopeEntry = namedtuple("ScopeEntry", ("type", "immutable", "value"))


class CodeGenerator(ASTVisitor):
    """Generates code from AST."""
    def __init__(self):
        super(CodeGenerator, self).__init__()
        self.scopes = [
            {
                "perf_ret": ScopeEntry(int_, False, None),
                "perf_ret_float": ScopeEntry(float_, False, None),
            }
        ]

        self.intrinsics = {"say": SayFunction(), "sqrt": SqrtFunction()}

        self.code = ""

    def emit(self, new_code):
        self.code += new_code

    def push_scope(self):
        self.emit("{\n")
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()
        self.emit("}\n")

    def get_scope_entry(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def type_name(self, type_):
        if isinstance(type_, BitfieldDefinition):
            type_ = int_

        return {int_: "int", float_: "float", object_: "object"}[type_]

    def visit_Constant(self, constant):
        if is_numeric(constant.type):
            self.emit(repr(constant.value))
        elif constant.type is str_:
            self.emit('"%s"' % constant.value.encode("unicode_escape").decode("utf8").replace('"', '\"'))
        else:
            assert False, "constant of unknown type %r" % constant.type

    def visit_FunctionCall(self, func_call):
        if isinstance(func_call.type, BitfieldDefinition):
            self.visit(func_call.arguments[0])
        else:
            self.intrinsics[func_call.function].codegen(self, func_call.arguments)

    def visit_VarRef(self, var_ref):
        entry = self.get_scope_entry(var_ref.name)
        if entry.immutable:
            self.visit(entry.value)
        else:
            self.emit(var_ref.name)

    def emit_binary_op(self, binop, op):
        self.emit("(")
        self.visit(binop.lhs)
        self.emit(op)
        self.visit(binop.rhs)
        self.emit(")")

    def visit_AddOp(self, binop):
        self.emit_binary_op(binop, "+")

    def visit_SubOp(self, binop):
        self.emit_binary_op(binop, "-")

    def visit_MulOp(self, binop):
        self.emit_binary_op(binop, "*")

    def visit_DivOp(self, binop):
        self.emit_binary_op(binop, "/")

    def visit_LessThanOp(self, binop):
        self.emit_binary_op(binop, "<")

    def visit_GreaterThanOp(self, binop):
        self.emit_binary_op(binop, ">")

    def visit_LessThanOrEqualToOp(self, binop):
        self.emit_binary_op(binop, "<=")

    def visit_GreaterThanOrEqualToOp(self, binop):
        self.emit_binary_op(binop, ">=")

    def visit_EqualToOp(self, binop):
        self.emit_binary_op(binop, "==")

    def visit_NotEqualToOp(self, binop):
        self.emit_binary_op(binop, "!=")

    def visit_LogicalAndOp(self, binop):
        self.emit_binary_op(binop, "&&")

    def visit_LogicalOrOp(self, binop):
        self.emit_binary_op(binop, "||")

    def visit_LogicalNotOp(self, a):
        self.emit("(!")
        self.visit(a.expression)
        self.emit(")")

    def visit_BitfieldAssignment(self, assignment):
        self.visit(assignment.variable)
        self.emit(" = ")
        self.visit(assignment.expression)

    def visit_Assignment(self, assignment, shadow=False):
        var_name = assignment.variable.name
        expr_type = assignment.expression.type

        try:
            entry = self.get_scope_entry(var_name)
            var_type = entry.type
        except KeyError:
            var_type = expr_type
            self.scopes[-1][var_name] = ScopeEntry(var_type, False, None)
            self.emit("%s " % self.type_name(var_type))

        self.visit(assignment.variable)
        self.emit(" = ")
        self.visit(assignment.expression)

    def visit_BitfieldAccess(self, bitfield_access):
        self.visit(bitfield_access.variable)
        self.emit("[%d, %d]" % bitfield_access.variable.type.get_member_limits(bitfield_access.member))

    def visit_EnumDefinition(self, enum_definition):
        for name, value in enum_definition.members:
            self.scopes[-1][name] = ScopeEntry(int_, True, Constant(value, int_))

    def visit_Block(self, block):
        self.push_scope()

        for statement in block.statements:
            old_length = len(self.code)
            self.visit(statement)
            if old_length < len(self.code) and self.code[-1] != ";" and self.code[-2:] != "}\n":
                self.emit(";\n")

        self.pop_scope()

    def visit_IfStmt(self, if_stmt):
        self.emit("if(")
        self.visit(if_stmt.condition)
        self.emit(")")
        self.visit(if_stmt.then_block)
        if if_stmt.else_part is not None:
            self.emit("else ")
            self.visit(if_stmt.else_part)

    def visit_WhileStmt(self, while_stmt):
        self.emit("while(")
        self.visit(while_stmt.condition)
        self.emit(")")
        self.visit(while_stmt.block)

    def visit_CodeLiteral(self, code_literal):
        self.emit(code_literal.code)

    def visit_BreakStmt(self, break_stmt):
        self.emit("break")


def compile_script(filename, code):
    code_generator = CodeGenerator()
    ast_, errors = parse(code)
    for lineno, message in errors:
        sys.stderr.write("%s:%d: %s\n" % (filename, lineno, message))

    ast_ = TypeAnnotator().visit(ast_)
    ast_ = CallInliner().visit(ast_)
    ast_ = StringInliner().visit(ast_)

    code_generator.visit(ast_)

    return code_generator.code
