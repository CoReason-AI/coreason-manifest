import timeit


def sort_key_attrgetter(lst):
    import operator

    return sorted(lst, key=operator.attrgetter("cid"))


def sort_key_lambda(lst):
    return sorted(lst, key=lambda x: x.cid)


class Obj:
    def __init__(self, cid):
        self.cid = cid


lst = [Obj(i) for i in range(1000, 0, -1)]

t_attrgetter = timeit.timeit(lambda: sort_key_attrgetter(lst), number=10000)
t_lambda = timeit.timeit(lambda: sort_key_lambda(lst), number=10000)

print(f"attrgetter: {t_attrgetter:.4f}s")
print(f"lambda: {t_lambda:.4f}s")
