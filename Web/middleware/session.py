from django.shortcuts import redirect
from backend.database import Database
import asyncio, re

class SessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._unauthorized_allowed = ['', 'login', 'redirect', 'static/.*', 'action/.*']
        self._regex_pattern = re.compile('^/(%s)$' % '|'.join(self._unauthorized_allowed))

    def __call__(self, request):
        if not self._regex_pattern.match(request.path):
            session_key = request.COOKIES.get('session_key')
            if session_key is None or not asyncio.run(Database.session_exists(session_key)):
                return redirect('login')

        response = self.get_response(request)
        return response