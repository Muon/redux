from redux.ast import ASTNode


class Visitor(object):
    "Implements the extrinsic Visitor pattern."

    def visit(self, node, *args, **kwargs):
        "Starts visiting node."
        visitor = self.generic_visit
        for cls in node.__class__.__mro__:
            meth_name = 'visit_' + cls.__name__
            try:
                visitor = getattr(self, meth_name)
                break
            except AttributeError:
                pass

        return visitor(node, *args, **kwargs)


class ASTVisitor(Visitor):
    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        print(node)
        for name, value in node.fields():
            print("\t%r %r" % (name, value))
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)

    def push_scope(self):
        pass

    def pop_scope(self):
        pass

    def visit_Block(self, block):
        self.push_scope()
        self.generic_visit(block)
        self.pop_scope()


class ASTTransformer(ASTVisitor):
    def generic_visit(self, node):
        for name, old_value in node.fields():
            old_value = getattr(node, name, None)
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, ASTNode):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, ASTNode):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, ASTNode):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, name)
                else:
                    setattr(node, name, new_node)
        return node

    def visit_Block(self, block):
        super(ASTTransformer, self).visit_Block(block)
        return block
