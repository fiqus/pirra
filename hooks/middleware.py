from hooks import hook


class HookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hook("hooks.before_request", request)
        response = self.get_response(request)
        hook("hooks.after_response", request, response)
        return response

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        for response in hook("hooks.process_view", request, view_func, view_args, view_kwargs):
            if response:
                return response
        return
