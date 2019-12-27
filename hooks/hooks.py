from collections import defaultdict


class Hook(object):
    def __init__(self):
        self._registry = defaultdict(list)

    def __call__(self, name, *args, **kwargs):
        return [h(*args, **kwargs) for h in self._registry[name]]

    def register(self, name, func):
        self._registry[name] += [func]

    def unregister(self, name, func):
        if func in self._registry[name]:
            self._registry[name].remove(func)

    def unregister_all(self, name):
        del self._registry[name][:]
