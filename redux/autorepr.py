import inspect
import os


class AutoRepr(object):
    """A mixin that defines __repr__ by introspecting on the constructor.

    If the constructor for a class Quux of the form::
      def __init__(self, foo, bar, baz):
    Then __repr__ will return something like::
      "%s(%r, %r, %r)" % (type(self).__name__, self.foo, self.bar, self.baz)

    This is useful when you are defining classes that are basically just
    structs, and you want them to print out a valid repr.  This is especially
    useful in combination with StructEq when writing tests, because you can
    copy and paste the actual value into the expected value and it will be
    valid Python.

    """

    def __repr__(self):
        pieces = []
        class_ = type(self)
        module = inspect.getmodule(class_)
        short_module_name = os.path.basename(module.__file__).split('.')[0]
        pieces.append(short_module_name)
        pieces.append('.')
        pieces.append(class_.__name__)
        pieces.append("(")
        if inspect.ismethod(self.__init__):
            (args, varargs, kwargs, defaults) = inspect.getargspec(self.__init__)
        else:
            # This means that the class has the default __init__ method with no
            # arguments.
            (args, varargs, kwargs, defaults) = ([], None, None, [])
        if defaults is None:
            defaults = []
        assert varargs is None and kwargs is None, 'AutoRepr does not support *args or **kwargs.'

        def special_getattr(field):
            # The idiom described in PEP 8 for avoiding collisions with reserved
            # words and buitins is to append '_' to to an identifier.  However,
            # since attributes can't collide with builtins, you see code like:
            # `self.type = type_`, which we allow for by checking for both
            # cases.
            if hasattr(self, field):
                value = getattr(self, field)
            elif field.endswith('_') and hasattr(self, field[:-1]):
                value = getattr(self, field[:-1])
            else:
                raise TypeError("AutoRepr can't find a field corresponding to "
                                "the __init__ argument %r." % arg)
            return value
        arg_strs = []
        # Deal with regular positional arguments.
        for arg in args[1:-len(defaults) if defaults else None]:
            arg_strs.append(repr(special_getattr(arg)))
        # Deal with optional keyword or default value arguments.
        for (default, arg) in zip(defaults, args[len(args) - len(defaults):]):
            value = special_getattr(arg)
            if value != default:
                arg_strs.append("%s=%r" % (arg, value))
        pieces.append(", ".join(arg_strs))
        pieces.append(")")
        return "".join(pieces)
