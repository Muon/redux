from collections import namedtuple
from copy import deepcopy
from redux.ast import FunctionDefinition, BitfieldDefinition, ReturnStmt, Assignment, VarRef
from redux.intrinsics import get_intrinsic_functions, IntrinsicFunction, GetAchronalField, SetAchronalField
from redux.types import is_numeric, common_arithmetic_type, check_assignable, int_, float_, str_, object_
from redux.visitor import ASTTransformer, ASTVisitor
from redux.objectattributes import CHRONAL_ATTRS, ACHRONAL_ATTRS


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


INITIAL_SCOPE = {
    "perf_ret": ScopeEntry(int_, False, None),
    "perf_ret_float": ScopeEntry(float_, False, None),
    "query": ScopeEntry(object_, False, None),
    "unit": ScopeEntry(object_, False, None),
    "player": ScopeEntry(object_, False, None),
    "target": ScopeEntry(object_, False, None),
    "ignore_collision_with_unit": ScopeEntry(object_, False, None),
    "query_vis_distance": ScopeEntry(int_, False, None),
    "min_action_ticks": ScopeEntry(int_, False, None),
    "ignore_moving_units_dist": ScopeEntry(int_, False, None),
    "goal_distance": ScopeEntry(int_, False, None),
}


class TypeAnnotator(ASTTransformer):
    """Annotates AST with type information."""
    def __init__(self):
        super(TypeAnnotator, self).__init__()
        self.scopes = [INITIAL_SCOPE.copy()]

        for name, intrinsic in get_intrinsic_functions():
            self.scopes[0][name] = ScopeEntry(IntrinsicFunction, True, intrinsic)

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
        return var_ref

    def visit_DottedAccess(self, dotted_access):
        dotted_access = self.generic_visit(dotted_access)

        if dotted_access.expression.type == object_:
            if dotted_access.member not in ACHRONAL_ATTRS:
                raise InvalidExpressionError(dotted_access)
        else:
            dotted_access.expression.type.get_member_limits(dotted_access.member)

        dotted_access.type = int_
        return dotted_access

    def visit_BitfieldAssignment(self, bitfield_assignment):
        bitfield_assignment = self.generic_visit(bitfield_assignment)

        if bitfield_assignment.expression.type != int_:
            raise IncompatibleTypeError(bitfield_assignment.expression.type)

        return bitfield_assignment

    def visit_FunctionDefinition(self, function_def):
        function_def.visible_scope = self.scopes[:]
        self.scopes[-1][function_def.name] = ScopeEntry(
            FunctionDefinition, True, function_def)
        return function_def

    def visit_BitfieldDefinition(self, bitfield_def):
        self.scopes[-1][bitfield_def.name] = ScopeEntry(
            BitfieldDefinition, True, bitfield_def)
        return bitfield_def

    def visit_EnumDefinition(self, enum_def):
        for name, value in enum_def.members:
            self.scopes[-1][name] = ScopeEntry(int_, True, value)
        return enum_def

    def visit_FunctionCall(self, func_call):
        func_call = self.generic_visit(func_call)

        entry = self.get_scope_entry(func_call.function)

        if entry.type is not FunctionDefinition:
            if entry.type is IntrinsicFunction:
                func_call.type = entry.value.type(func_call.arguments)
                func_call.func_def = entry.value
            elif entry.type is BitfieldDefinition:
                func_call.type = entry.value
                func_call.func_def = entry.value
                func_call.func_def.nontrivial = False
            else:
                raise NotCallableError(func_call.function)
            return func_call

        func_def = deepcopy(entry.value)

        if len(func_call.arguments) != len(func_def.arguments):
            raise InvalidExpressionError(
                "expected %d arguments, got %d" % (len(func_def.arguments),
                                                   len(func_call.arguments)))

        shadowed_vars = [Assignment(VarRef(name), value, True)
                         for name, value
                         in zip(func_def.arguments, func_call.arguments)]
        new_statements = shadowed_vars + func_def.block.statements
        func_def.block.statements = new_statements

        real_scopes = self.scopes
        self.scopes = func_def.visible_scope

        func_def.block = self.visit(func_def.block)

        if new_statements and isinstance(new_statements[-1], ReturnStmt):
            func_call.type = new_statements[-1].expression.type
        else:
            func_call.type = None

        self.scopes = real_scopes

        func_call.func_def = func_def
        return func_call

    def visit_Assignment(self, assignment):
        assignment.expression = self.visit(assignment.expression)
        expr_type = assignment.expression.type
        if expr_type is None:
            raise UndefinedTypeError(assignment.expression)

        var_name = assignment.variable.name

        try:
            if assignment.declare is True:
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

        assignment.variable = self.visit(assignment.variable)

        return assignment

    def visit_BinaryOp(self, binop):
        binop = self.generic_visit(binop)

        if is_numeric(binop.lhs.type) and is_numeric(binop.rhs.type):
            binop.type = common_arithmetic_type(binop.lhs.type, binop.rhs.type)
        else:
            raise InvalidExpressionError(binop)

        return binop

    def visit_NegateOp(self, negop):
        negop = self.generic_visit(negop)

        if negop.expression.type != int_:
            raise InvalidExpressionError(negop)

        negop.type = int_

        return negop


    def visit_BitwiseOp(self, bitop):
        bitop = self.generic_visit(bitop)

        for child in bitop.children():
            if child.type != int_:
                raise InvalidExpressionError(bitop)

        bitop.type = int_

        return bitop

    def visit_RelationalOp(self, relop):
        relop = self.generic_visit(relop)

        for child in relop.children():
            if not is_numeric(child.type):
                raise InvalidExpressionError(relop)

        relop.type = int_

        return relop

    def handle_equality(self, eqop):
        eqop = self.generic_visit(eqop)
        # You can always compare equal things of the same type (e.g. ints and
        # ints, and objects and objects), otherwise they must both be numeric.
        if eqop.lhs.type != eqop.rhs.type:
            if not is_numeric(eqop.lhs.type) or not is_numeric(eqop.rhs.type):
                raise IncompatibleTypeError(eqop)
        eqop.type = int_
        return eqop

    def visit_EqualToOp(self, eqop):
        return self.handle_equality(eqop)

    def visit_NotEqualToOp(self, eqop):
        return self.handle_equality(eqop)

    def handle_connective(self, connective):
        connective = self.generic_visit(connective)
        # Logical connectives are always well-defined for all three types.
        connective.type = int_
        return connective

    def visit_LogicalAndOp(self, land):
        return self.handle_connective(land)

    def visit_LogicalOrOp(self, lor):
        return self.handle_connective(lor)

    def visit_LogicalNotOp(self, lnot):
        return self.handle_connective(lnot)

    def visit_ChronalAccess(self, chronal_access):
        chronal_access = self.generic_visit(chronal_access)
        if (chronal_access.object.type != object_ or
            chronal_access.member not in CHRONAL_ATTRS):
            raise InvalidExpressionError(chronal_access)

        chronal_access.type = int_

        return chronal_access

    def visit_ClassAccess(self, class_access):
        class_access = self.generic_visit(class_access)
        if (class_access.class_.type != int_ or
            class_access.member not in ACHRONAL_ATTRS):
            raise InvalidExpressionError(class_access)

        class_access.type = int_

        return class_access

    def visit_Query(self, query):
        class BestMoveEliminator(ASTVisitor):
            def visit_Query(self, node):
                if node.type == "BESTMOVE":
                    raise InvalidExpressionError("QUERY BESTMOVE as subquery")

        for child in query.children():
            BestMoveEliminator().visit(child)

        self.generic_visit(query)

        if not is_numeric(query.op_expr.type):
            raise InvalidExpressionError(
                "operation clause has invalid type %s" % query.op_expr.type)

        if not is_numeric(query.where_cond.type):
            raise InvalidExpressionError(
                "WHERE clause has invalid type %s" % query.where_cond.type)

        if query.query_type == "UNIT":
            query.type = object_
        else:
            query.type = int_

        return query
