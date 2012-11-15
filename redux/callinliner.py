from redux.ast import (Block, Assignment, WhileStmt, IfStmt, BreakStmt,
                       ReturnStmt, Constant, VarRef)
from redux.types import int_
from redux.visitor import ASTVisitor


class CallInliner(ASTVisitor):
    """Inlines all calls to nontrivial functions."""
    def __init__(self):
        super(CallInliner, self).__init__()
        self.block_stack = []
        self.return_value_counter = 0

    def allocate_temporary(self, type_):
        temporary = VarRef("__retval%d" % self.return_value_counter)
        temporary.type = type_
        self.block_stack[-1].append(Assignment(temporary, Constant(0, type_)))
        self.return_value_counter += 1
        return temporary

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

    def visit_WhileStmt(self, while_stmt):
        new_block = self.visit(Block([IfStmt(while_stmt.condition,
                                             while_stmt.block,
                                             Block([BreakStmt()]))]))
        return WhileStmt(Constant(1, int_), new_block)

    def visit_FunctionCall(self, func_call):
        func_def = func_call.func_def

        func_call.arguments = [self.visit(arg) for arg in func_call.arguments]

        if not func_def.nontrivial:
            return func_call

        new_block = func_def.block

        if new_block.statements and isinstance(new_block.statements[-1], ReturnStmt):
            return_var = self.allocate_temporary(func_call.type)
            return_expr = new_block.statements[-1].expression
            new_block.statements[-1] = Assignment(return_var, return_expr)
        else:
            return_var = None

        self.block_stack[-1].append(new_block)

        return return_var
