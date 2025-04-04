from django.utils.deprecation import MiddlewareMixin

class CustomHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        return response