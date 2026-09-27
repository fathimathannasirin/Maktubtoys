from django.conf import settings


class MarkHttpsBehindProxyMiddleware:
    """Treat production traffic as HTTPS so CSRF/session cookies match the live site."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
            request.META['wsgi.url_scheme'] = 'https'
        return self.get_response(request)
