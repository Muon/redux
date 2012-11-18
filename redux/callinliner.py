from redux.ast import (Block, Assignment, WhileStmt, IfStmt, BreakStmt,
                       ReturnStmt, Constant, VarRef, Stmt)
from redux.types import int_
from redux.visitor import ASTTransformer


class CallInliner(ASTTransformer):
    """Inlines all calls to nontrivial functions."""
    def __init__(self):
        super(CallInliner, self).__init__()
        self.prepend_stack = []
        self.return_value_counter = 0

    def allocate_temporary(self, type_):
        temporary = VarRef("__retval%d" % self.return_value_counter)
        temporary.type = type_
        self.prepend_stmt(Assignment(temporary, Constant(0, type_)))
        self.return_value_counter += 1
        return temporary

    def prepend_stmt(self, stmt):
        self.prepend_stack[-1].append(stmt)

    def generic_visit(self, node):
        if isinstance(node, Stmt):
            self.prepend_stack.append([])

        result = super(CallInliner, self).generic_visit(node)

        if isinstance(node, Stmt):
            new_statements = self.prepend_stack.pop()
            if result is not None:
                new_statements.append(result)

            return new_statements
        else:
            return result

    def visit_WhileStmt(self, while_stmt):
        new_block = self.visit(Block([IfStmt(while_stmt.condition,
                                             while_stmt.block,
                                             Block([BreakStmt()]))]))
        return WhileStmt(Constant(1, int_), new_block)

    def visit_FunctionDefinition(self, func_def):
        pass

    def visit_FunctionCall(self, func_call):
        self.generic_visit(func_call)

        func_def = func_call.func_def

        if not func_def.nontrivial:
            return func_call

        new_block = func_def.block
        self.visit(new_block)

        new_statements = new_block.statements

        if new_statements and isinstance(new_statements[-1], ReturnStmt):
            return_var = self.allocate_temporary(func_call.type)
            return_expr = new_statements[-1].expression
            new_statements[-1] = Assignment(return_var, return_expr)
            self.prepend_stmt(new_block)
            return return_var
        else:
            return new_block
