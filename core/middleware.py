from threading import local

_thread_local = local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request
        response = self.get_response(request)

        if hasattr(_thread_local, 'request'):
            del _thread_local.request
        return response

def get_current_request():
    return getattr(_thread_local, 'request', None)

class SSEMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if response.get('Content-Type') == 'text/event-stream':
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            
            if 'auth_token' in request.GET:
                pass
                
        return response