from collections import namedtuple
from copy import deepcopy
from redux.ast import FunctionDefinition, BitfieldDefinition, ReturnStmt, Assignment, VarRef
from redux.intrinsics import IntrinsicFunction, SayFunction, SqrtFunction, GetAchronalField, SetAchronalField
from redux.types import is_numeric, common_arithmetic_type, check_assignable, int_, float_, str_
from redux.visitor import ASTVisitor


ScopeEntry = namedtuple("ScopeEntry", ("type", "immutable", "value"))


class UndefinedVariableError(KeyError):
    pass


class UndefinedTypeError(TypeError):
    pass


class IncompatibleTypeError(TypeError):
    pass


class NotCallableError(TypeError):
    pass


class InvalidExpressionError(TypeError):
    pass


class ImmutabilityViolationError(TypeError):
    pass

class TypeAnnotator(ASTVisitor):
    """Annotates AST with type information."""
    def __init__(self):
        super(TypeAnnotator, self).__init__()
        self.scopes = [
            {
                "perf_ret": ScopeEntry(int_, False, None),
                "perf_ret_float": ScopeEntry(float_, False, None),
                "say": ScopeEntry(IntrinsicFunction, True, SayFunction()),
                "sqrt": ScopeEntry(IntrinsicFunction, True, SqrtFunction())
            }
        ]

        self.visit(GetAchronalField())
        self.visit(SetAchronalField())

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def get_scope_entry(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise UndefinedVariableError(name)

    def get_variable_type(self, name):
        return self.get_scope_entry(name).type

    def visit_VarRef(self, var_ref):
        var_ref.type = self.get_variable_type(var_ref.name)

    def visit_BitfieldAccess(self, bitfield_access):
        self.visit(bitfield_access.variable)
        bitfield_access.variable.type.get_member_limits(bitfield_access.member)
        bitfield_access.type = int_

    def visit_BitfieldAssignment(self, bitfield_assignment):
        self.visit(bitfield_assignment.variable)
        self.visit(bitfield_assignment.expression)

        if bitfield_assignment.expression.type != int_:
            raise IncompatibleTypeError(bitfield_assignment.expression.type)

    def visit_FunctionDefinition(self, function_def):
        function_def.visible_scope = self.scopes[:]
        self.scopes[-1][function_def.name] = ScopeEntry(FunctionDefinition, True, function_def)

    def visit_BitfieldDefinition(self, bitfield_def):
        self.scopes[-1][bitfield_def.name] = ScopeEntry(BitfieldDefinition, True, bitfield_def)

    def visit_EnumDefinition(self, enum_def):
        for name, value in enum_def.members:
            self.scopes[-1][name] = ScopeEntry(int_, True, value)

    def visit_FunctionCall(self, func_call):
        for argument in func_call.arguments:
            self.visit(argument)

        entry = self.get_scope_entry(func_call.function)

        if entry.type is not FunctionDefinition:
            if entry.type is IntrinsicFunction:
                func_call.type = entry.value.type
                func_call.func_def = entry.value
            elif entry.type is BitfieldDefinition:
                func_call.type = entry.value
                func_call.func_def = entry.value
                func_call.func_def.nontrivial = False
            else:
                raise NotCallableError(func_call.function)
            return

        func_def = deepcopy(entry.value)

        if len(func_call.arguments) != len(func_def.arguments):
            raise InvalidExpressionError("expected %d arguments, got %d" % (len(func_def.arguments),
                                                                            len(func_call.arguments)))

        shadowed_vars = [Assignment(VarRef(name), value, True)
                         for name, value
                         in zip(func_def.arguments, func_call.arguments)]
        func_def.block.statements = shadowed_vars + func_def.block.statements

        real_scopes = self.scopes
        self.scopes = func_def.visible_scope

        self.visit(func_def.block)

        if func_def.block.statements and \
           isinstance(func_def.block.statements[-1], ReturnStmt):
            func_call.type = func_def.block.statements[-1].expression.type
        else:
            func_call.type = None

        self.scopes = real_scopes

        func_call.func_def = func_def

    def visit_Assignment(self, assignment):
        self.visit(assignment.expression)
        expr_type = assignment.expression.type
        if expr_type is None:
            raise UndefinedTypeError(assignment.expression)

        var_name = assignment.variable.name

        try:
            if assignment.shadow is True:
                raise KeyError

            type_, immutable, value = self.get_scope_entry(var_name)

            if not check_assignable(expr_type, type_):
                raise IncompatibleTypeError(expr_type, type_)

            if immutable is True:
                raise ImmutabilityViolationError(var_name)
        except KeyError:
            if expr_type == str_:
                self.scopes[-1][var_name] = ScopeEntry(expr_type, True,
                                                       assignment.expression)
            else:
                self.scopes[-1][var_name] = ScopeEntry(expr_type, False, None)

    def visit_BinaryOp(self, binop):
        self.visit(binop.lhs)
        self.visit(binop.rhs)

        if is_numeric(binop.lhs.type) and is_numeric(binop.rhs.type):
            binop.type = common_arithmetic_type(binop.lhs.type, binop.rhs.type)
        else:
            raise InvalidExpressionError(binop)

    def visit_RelationalOp(self, relop):
        self.visit(relop.lhs)
        self.visit(relop.rhs)

        if is_numeric(relop.lhs.type) and is_numeric(relop.rhs.type):
            relop.type = int_
        else:
            raise InvalidExpressionError(relop)

    def visit_LogicalNotOp(self, lnotop):
        self.visit(lnotop.expression)

        if is_numeric(lnotop.expression.type):
            lnotop.type = int_
        else:
            raise InvalidExpressionError(lnotop)
