import traceback

from authentication.models import ErrorLog


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        ErrorLog.objects.create(
            error_type=type(exception).__name__,
            error_message=str(exception),
            traceback=traceback.format_exc(),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            user_ip=request.META.get("REMOTE_ADDR"),
            user=request.user if request.user.is_authenticated else None,
        )
