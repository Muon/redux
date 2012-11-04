import sys
from redux.ast import (FunctionCall, Constant, VarRef, BinaryOp, RelationalOp,
                       BitfieldDefinition, EnumDefinition, BitfieldAccess)
from redux.callinliner import CallInliner
from redux.intrinsics import SayFunction, SqrtFunction
from redux.parser import parse
from redux.visitor import ASTVisitor


class UndefinedVariableError(KeyError):
    pass


class CodeGenerator(ASTVisitor):
    """Generates code from AST."""
    def __init__(self):
        super(CodeGenerator, self).__init__()
        self.local_scopes = [{"perf_ret": int, "perf_ret_float": float}]
        self.strings = []
        self.enums = []
        self.bitfield_definitions = []
        self.intrinsics = {"say": SayFunction(), "sqrt": SqrtFunction()}

        self.code = ""

    def emit(self, new_code):
        self.code += new_code

    def push_scope(self):
        self.emit("{\n")
        self.local_scopes.append({})
        self.strings.append({})
        self.bitfield_definitions.append({})
        self.enums.append({})

    def pop_scope(self):
        self.enums.pop()
        self.bitfield_definitions.pop()
        self.strings.pop()
        self.local_scopes.pop()
        self.emit("}\n")

    def get_variable_type(self, name):
        try:
            return self._scope_search(self.local_scopes, name)
        except KeyError:
            raise UndefinedVariableError(name)

    def get_string_by_name(self, name):
        return self._scope_search(self.strings, name)

    def get_bitfield_definition_by_name(self, name):
        return self._scope_search(self.bitfield_definitions, name)

    def get_enum_value_by_name(self, name):
        return self._scope_search(self.enums, name)

    def _scope_search(self, scope_list, name):
        for scope in reversed(scope_list):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def is_name_defined(self, name):
        try:
            self.get_variable_type(name)
            return True
        except UndefinedVariableError:
            return False

    def common_type(self, a, b):
        a_type = self.expression_type(a)
        b_type = self.expression_type(b)

        if a_type is b_type:
            return a_type

        if a_type is float or b_type is float:
            return float

        raise RuntimeError("no common type for %s and %s (%r and %r)" % (a_type, b_type, a, b))

    def expression_type(self, expression):
        if isinstance(expression, Constant):
            return type(expression.value)

        if isinstance(expression, BitfieldAccess):
            return int

        if isinstance(expression, RelationalOp):
            return int

        if isinstance(expression, BinaryOp):
            return self.common_type(expression.lhs, expression.rhs)

        if isinstance(expression, VarRef):
            return self.get_variable_type(expression.name)

        if isinstance(expression, FunctionCall):
            try:
                return self.get_bitfield_definition_by_name(expression.function)
            except KeyError:
                return self.intrinsics[expression.function].type(self, expression.arguments)

        raise RuntimeError("could not determine type of expression %r" % expression)

    def are_types_compatible(self, a, b):
        if a is b:
            return True

        if (a is int or a is float) and (b is int or b is float):
            return True

        raise RuntimeError("types %r and %r are not compatible" % (a, b))

    def type_name(self, type_):
        return {int: "int", float: "float", object: "object"}[type_]

    def visit_Constant(self, constant):
        self.emit(str(constant.get_value()))

    def visit_FunctionCall(self, func_call):
        try:
            self.get_bitfield_definition_by_name(func_call.function)
            self.visit(func_call.arguments[0])
        except KeyError:
            self.intrinsics[func_call.function].codegen(self, func_call.arguments)

    def visit_VarRef(self, var_ref):
        var_type = self.get_variable_type(var_ref.name)
        if var_type is str:
            self.visit(self.get_string_by_name(var_ref.name))
        elif isinstance(var_type, EnumDefinition):
            self.visit(self.get_enum_value_by_name(var_ref.name))
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

    def visit_Assignment(self, assignment, shadow=False):
        if isinstance(assignment.variable, BitfieldAccess):
            bitfield_access = assignment.variable
            variable = bitfield_access.variable
            start, length = self.get_variable_type(variable.name).get_member_limits(bitfield_access.member)
            self.emit("%s[%d, %d] = " % (variable.name, start, length))
            self.visit(assignment.expression)
            self.emit(";\n")
        else:
            var_name = assignment.variable.name
            expr_type = self.expression_type(assignment.expression)
            if shadow or not self.is_name_defined(var_name):
                self.local_scopes[-1][var_name] = expr_type
                output_type = expr_type

                if isinstance(output_type, BitfieldDefinition):
                    output_type = int

                if isinstance(output_type, EnumDefinition):
                    output_type = int

                if output_type is not str:
                    self.emit("%s " % self.type_name(output_type))

            var_type = self.get_variable_type(var_name)
            if self.are_types_compatible(var_type, expr_type):
                if expr_type is str:
                    self.strings[-1][var_name] = assignment.expression
                else:
                    self.emit("%s = " % var_name)
                    self.visit(assignment.expression)
                    self.emit(";\n")
            else:
                raise RuntimeError("can't assign %s to %s" % (expr_type, var_type))

    def visit_BitfieldDefinition(self, bitfield_definition):
        self.bitfield_definitions[-1][bitfield_definition.name] = bitfield_definition

    def visit_BitfieldAccess(self, bitfield_access):
        self.visit(bitfield_access.variable)
        self.emit("[%d, %d]" % self.expression_type(bitfield_access.variable).get_member_limits(bitfield_access.member))

    def visit_EnumDefinition(self, enum_definition):
        for name, value in enum_definition.members:
            self.enums[-1][name] = Constant(value)
            self.local_scopes[-1][name] = enum_definition

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
