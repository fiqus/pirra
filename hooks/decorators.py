from hooks import hook


def hook_receiver(name):
    def decorator_func(func):
        hook.register(name, func)
        return func
    return decorator_func
