import sys
from collections import namedtuple
from redux.ast import (FunctionCall, Constant, VarRef, BinaryOp, RelationalOp,
                       BitfieldDefinition, BitfieldAccess)
from redux.callinliner import CallInliner
from redux.intrinsics import SayFunction, SqrtFunction
from redux.parser import parse
from redux.types import str_, float_, int_, object_, is_numeric
from redux.visitor import ASTVisitor


class UndefinedVariableError(KeyError):
    pass


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

    def get_var_ref_type(self, var_ref):
        try:
            return self.get_scope_entry(var_ref.name).type
        except KeyError:
            raise UndefinedVariableError(var_ref.name)

    def get_scope_entry(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def common_type(self, a, b):
        a_type = self.expression_type(a)
        b_type = self.expression_type(b)

        if is_numeric(a_type) and is_numeric(b_type):
            if a_type is int_ and b_type is int_:
                return int_

            if a_type is float_ or b_type is float_:
                return float_

        raise TypeError("no common type for %s and %s (%r and %r)" % (a_type, b_type, a, b))

    def expression_type(self, expression):
        if isinstance(expression, Constant):
            return expression.type

        if isinstance(expression, BitfieldAccess):
            return int_

        if isinstance(expression, RelationalOp):
            return int_

        if isinstance(expression, BinaryOp):
            return self.common_type(expression.lhs, expression.rhs)

        if isinstance(expression, VarRef):
            return self.get_var_ref_type(expression)

        if isinstance(expression, FunctionCall):
            try:
                entry = self.get_scope_entry(expression.function)
                if entry.type is BitfieldDefinition:
                    return entry.value
            except KeyError:
                pass

            return self.intrinsics[expression.function].type(self, expression.arguments)

        raise TypeError("could not determine type of %r" % expression)

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
        try:
            entry = self.get_scope_entry(func_call.function)
            if entry.type is not BitfieldDefinition:
                raise TypeError("'%s' is not a type" % func_call.function)
            self.visit(func_call.arguments[0])
        except KeyError:
            self.intrinsics[func_call.function].codegen(self, func_call.arguments)

    def visit_VarRef(self, var_ref):
        try:
            entry = self.get_scope_entry(var_ref.name)
        except KeyError:
            raise UndefinedVariableError(var_ref.name)

        if entry.immutable:
            self.visit(entry.value)
        else:
            self.emit(var_ref.name)

    def emit_binary_op(self, binop, op):
        self.common_type(binop.lhs, binop.rhs)

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

    # Variables being assigned to must have the proper type, or be unused.
    #
    # Possibilities:
    # - assign int/float to variable
    # - assign int to bitfield member
    # - assign string to an *unused* variable
    #
    # Procedure:
    # 1. Verify validity of assignment.
    # 2. Output assignment, if the expression is not a string.

    def visit_BitfieldAssignment(self, assignment):
        if self.expression_type(assignment.expression) is not int_:
            raise TypeError("only int maybe assigned to a bitfield member")

        self.visit(assignment.variable)
        self.emit(" = ")
        self.visit(assignment.expression)
        self.emit(";\n")

    def visit_Assignment(self, assignment, shadow=False):
        var_name = assignment.variable.name
        expr_type = self.expression_type(assignment.expression)

        try:
            entry = self.get_scope_entry(var_name)
            if entry.immutable:
                if entry.type is str_:
                    raise TypeError("strings may not be mutated")
                else:
                    raise TypeError("attempt to modify immutable variable")
            var_type = entry.type
        except KeyError:
            var_type = expr_type
            if expr_type is str_:
                self.scopes[-1][var_name] = ScopeEntry(var_type, True, assignment.expression)
            else:
                self.scopes[-1][var_name] = ScopeEntry(var_type, False, None)
                self.emit("%s " % self.type_name(var_type))
        else:  # Variable exists
            if is_numeric(var_type) or is_numeric(expr_type):
                if not(is_numeric(var_type) and is_numeric(expr_type)):
                    raise TypeError("cannot assign %r to %r" % (expr_type, var_type))

        assert is_numeric(expr_type) or expr_type is str_ or isinstance(expr_type, BitfieldDefinition), "%r (%r)" % (expr_type, assignment.expression)
        assert is_numeric(var_type) or var_type is str_ or isinstance(var_type, BitfieldDefinition), "%r (%r)" % (var_type, assignment.variable)

        if expr_type is not str_:
            self.visit(assignment.variable)
            self.emit(" = ")
            self.visit(assignment.expression)
            self.emit(";\n")

    def visit_BitfieldDefinition(self, bitfield_definition):
        self.scopes[-1][bitfield_definition.name] = ScopeEntry(BitfieldDefinition, True, bitfield_definition)

    def visit_BitfieldAccess(self, bitfield_access):
        self.visit(bitfield_access.variable)
        self.emit("[%d, %d]" % self.get_var_ref_type(bitfield_access.variable).get_member_limits(bitfield_access.member))

    def visit_EnumDefinition(self, enum_definition):
        for name, value in enum_definition.members:
            self.scopes[-1][name] = ScopeEntry(int_, True, Constant(value, int_))

    def visit_Block(self, block):
        self.push_scope()

        for assignment in block.scope_overrides:
            self.visit(assignment, True)

        for statement in block.statements:
            self.visit(statement)
            if isinstance(statement, FunctionCall):
                if not self.intrinsics[statement.function].nontrivial:
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
        self.emit("break;\n")


def compile_script(filename, code):
    code_generator = CodeGenerator()
    ast_, errors = parse(code)
    for lineno, message in errors:
        sys.stderr.write("%s:%d: %s\n" % (filename, lineno, message))

    code_generator.visit(CallInliner().visit(ast_))
    return code_generator.code
