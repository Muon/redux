from redux.ast import (Block, Assignment, WhileStmt, IfStmt, BreakStmt,
                       ReturnStmt, Constant, VarRef)
from redux.intrinsics import IntrinsicFunction, SetAchronalField, GetAchronalField
from redux.types import int_
from redux.visitor import ASTVisitor


class CallInliner(ASTVisitor):
    """Inlines all calls to nontrivial functions."""
    def __init__(self):
        super(CallInliner, self).__init__()
        self.local_scopes = [{"__set_achronal_field": SetAchronalField(), "__get_achronal_field": GetAchronalField()}]
        self.block_stack = []
        self.return_value_counter = 0

    def push_scope(self):
        self.local_scopes.append({})

    def pop_scope(self):
        self.local_scopes.pop()

    def allocate_temporary(self):
        temporary = VarRef("__retval%d" % self.return_value_counter)
        self.block_stack[-1].append(Assignment(temporary, Constant(0, int_)))
        self.return_value_counter += 1
        return temporary

    def find_function_by_name(self, name):
        for scope in reversed(self.local_scopes):
            if name in scope:
                return scope[name]

        # Assume it's intrinsic; it will raise an exception later if it's not.
        return IntrinsicFunction()

    def visit_ASTNode(self, node):
        return node

    def visit_Block(self, block):
        self.push_scope()

        new_statements = []
        self.block_stack.append(new_statements)
        for statement in block.statements:
            new_statement = self.visit(statement)
            if new_statement is not None:
                new_statements.append(new_statement)

        block.statements = new_statements
        self.block_stack.pop()

        self.pop_scope()

        return block

    def visit_BinaryOp(self, binop):
        binop.lhs = self.visit(binop.lhs)
        binop.rhs = self.visit(binop.rhs)
        return binop

    def visit_Assignment(self, assignment):
        assignment.expression = self.visit(assignment.expression)
        return assignment

    def visit_FunctionDefinition(self, func_def):
        self.local_scopes[-1][func_def.name] = func_def
        return func_def

    def visit_IfStmt(self, if_stmt):
        if_stmt.condition = self.visit(if_stmt.condition)
        if_stmt.then_block = self.visit(if_stmt.then_block)

        if if_stmt.else_part is not None:
            if_stmt.else_part = self.visit(if_stmt.else_part)

        return if_stmt

    def visit_WhileStmt(self, while_stmt):
        new_block = self.visit(Block([IfStmt(while_stmt.condition,
                                             while_stmt.block,
                                             Block([BreakStmt()]))]))
        return WhileStmt(Constant(1, int_), new_block)

    def visit_FunctionCall(self, func_call):
        new_arguments = []
        for argument in func_call.arguments:
            new_arguments.append(self.visit(argument))
        func_call.arguments = new_arguments

        function = self.find_function_by_name(func_call.function)

        if function.nontrivial:
            if len(func_call.arguments) != len(function.arguments):
                raise RuntimeError("expected %d arguments, got %d" %
                                   (len(func_call.arguments),
                                    len(function.arguments)))

            overrides = [Assignment(VarRef(a), b) for a, b in zip(function.arguments,
                                                                  func_call.arguments)]
            new_block = Block(function.block.statements[:], overrides)

            return_var = None

            if new_block.statements and isinstance(new_block.statements[-1], ReturnStmt):
                return_var = self.allocate_temporary()
                return_expr = new_block.statements[-1].expression
                new_block.statements[-1] = Assignment(return_var, return_expr)

            self.visit(new_block)

            self.block_stack[-1].append(new_block)
            if return_var is not None:
                return return_var
            else:
                return None
        else:
            return func_call
