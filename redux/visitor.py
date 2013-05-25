from redux.ast import ASTNode
import logging


class Visitor(object):
    "Implements the extrinsic Visitor pattern."
    def __init__(self):
        super(Visitor, self).__init__()
        self.depth = 0

    def log(self, fmt, *args, **kwargs):
        logging.getLogger(type(self).__name__).debug("%s%d: " + fmt, "    " * self.depth, self.depth, *args, **kwargs)

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

        self.log("Visiting child: %r", node)
        self.depth += 1
        result = visitor(node, *args, **kwargs)
        self.log("Leaving node: %r", node)
        self.depth -= 1
        return result


class ASTVisitor(Visitor):
    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for name, value in node.fields():
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
