from redux.ast import (Block, Assignment, WhileStmt, IfStmt, BreakStmt,
                       ReturnStmt, Constant, VarRef, Stmt, NoOp, FunctionCall)
from redux.types import int_, object_
from redux.visitor import ASTTransformer, ASTVisitor


class CallInliner(ASTTransformer):
    """Inlines all calls to nontrivial functions."""
    def __init__(self):
        super(CallInliner, self).__init__()
        self.prepend_stack = []
        self.return_value_counter = 0

    def allocate_temporary(self, type_):
        temporary = VarRef("__retval%d" % self.return_value_counter)
        temporary.type = type_
        if type_ == object_:
            expr = FunctionCall("object", [Constant(0, int_)])
            expr.type = object_
        else:
            expr = Constant(0, type_)
        self.prepend_stmt(Assignment(temporary, expr, True))
        self.return_value_counter += 1
        return temporary

    def push_prepend_ctx(self):
        self.prepend_stack.append([])

    def pop_prepend_ctx(self):
        return self.prepend_stack.pop()

    def prepend_stmt(self, stmt):
        """Insert a statement before the one currently being processed."""
        self.log("Requesting prepend of %r", stmt)
        self.prepend_stack[-1].append(stmt)

    def visit_Stmt(self, node):
        self.push_prepend_ctx()
        self.log("New generic statement: %r", node)
        result = super(CallInliner, self).generic_visit(node)
        new_statements = self.pop_prepend_ctx()
        if result is not None:
            new_statements.append(result)
        self.log("Replacing statement with statement(s): %r", new_statements)
        return new_statements

    def visit_ForStmt(self, for_stmt):
        class NontrivialFunctionCheck(ASTVisitor):
            def visit_FunctionCall(self, func_call):
                if func_call.func_def.nontrivial is True:
                    raise RuntimeError

        self.push_prepend_ctx()

        for_stmt.block = self.visit(for_stmt.block)

        try:
            NontrivialFunctionCheck().visit(for_stmt.step_expr)
        except RuntimeError:
            for_stmt.block = self.visit(Block([for_stmt.block, for_stmt.step_expr]))
            for_stmt.step_expr = None

        try:
            NontrivialFunctionCheck().visit(for_stmt.condition)
        except RuntimeError:
            for_stmt.block = self.visit(Block([IfStmt(for_stmt.condition, for_stmt.block, Block([BreakStmt()]))]))
            for_stmt.condition = None

        try:
            NontrivialFunctionCheck().visit(for_stmt.assignment)
        except RuntimeError:
            self.log("Non-trivial assignment in for loop")
            for_stmt.assignment.expression = self.visit(for_stmt.assignment.expression)

        return self.pop_prepend_ctx() + [for_stmt]

    def visit_WhileStmt(self, while_stmt):
        new_block = self.visit(Block([IfStmt(while_stmt.condition,
                                             while_stmt.block,
                                             Block([BreakStmt()]))]))
        return WhileStmt(Constant(1, int_), new_block)

    def visit_FunctionDefinition(self, func_def):
        return None

    def visit_FunctionCall(self, func_call):
        self.generic_visit(func_call)

        func_def = func_call.func_def

        if not func_def.nontrivial:
            return func_call

        new_block = func_def.block
        argument_assignments = [Assignment(VarRef(name), value, True)
            for name, value in zip(func_def.arguments, func_call.arguments)]
        new_statements = argument_assignments + new_block.statements
        new_block.statements = new_statements
        self.visit(new_block)

        # If we have something like a = f(x), we have to insert the function
        # body *before* the assignment, then use a temporary return variable to
        # save the result of the function call.
        if new_statements and isinstance(new_statements[-1], ReturnStmt):
            return_var = self.allocate_temporary(func_call.type)
            self.log("Function call return var: %r", return_var)
            return_expr = new_statements[-1].expression
            new_statements[-1] = Assignment(return_var, return_expr)
            self.prepend_stmt(new_block)
            return return_var
        else:
            # Function is empty or does not contain a return statement.
            self.prepend_stmt(new_block)
            return NoOp()
