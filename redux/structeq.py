class StructEq(object):
    """A simple mixin that defines equality based on the objects attributes.

    This class is especially useful if you're in a situation where one object
    might not have all the attributes of the other, and your __eq__ method
    would otherwise have to remember to deal with that.

    Classes extending StructEq should only be used in hash tables if all of the
    class members are also hashable.

    Also, classes extending StructEq should not create a cyclic graph where all
    nodes in the cycle extend StructEq, or there will be an infinite loop.
    Cycles are allowed, but objects creating cycles should have their own
    __eq__ methods that prevent the infinite loop.

    To designate certain attributes that shouldn't be checked for equality,
    override the class level variable NONEQ_ATTRS with the set of attrs you
    don't want to check.

    """

    NONEQ_ATTRS = frozenset()

    def __eq__(self, other):
        """Return True if of the same type and all attributes are equal."""
        if self is other:
            return True
        if type(self) != type(other):
            return False
        if len(self.__dict__) != len(other.__dict__):
            return False
        keys = ((frozenset(self.__dict__.keys()) |
                 frozenset(other.__dict__.keys())) - self.NONEQ_ATTRS)
        for key in keys:
            left_elt = self.__dict__.get(key)
            right_elt = other.__dict__.get(key)
            if not (left_elt == right_elt):
                return False
        return True

    def __ne__(self, other):
        """Return False if of different types or any attributes are unequal."""
        return not (self == other)

    def __hash__(self):
        """Return a reasonable hash value that uses all object attributes."""
        # We use frozenset here, because if we used tuple, the order of the
        # items in the tuple would be determined by the order in which the items
        # were returned, which depends on the order in which they were added to
        # __dict__.  Using frozenset fixes this, because it imposes an ordering
        # based on the items themselves, rather than the keys.
        return hash(frozenset(self.__dict__.items()))
