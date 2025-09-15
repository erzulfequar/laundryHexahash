from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import resolve
from .models import LogoutLog
from .signals import get_client_ip

class BranchMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'staff'):
            request.branch = request.user.staff.branch
        else:
            request.branch = None



class LogoutLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and resolve(request.path_info).url_name == 'logout':
            ip = get_client_ip(request)
            LogoutLog.objects.create(user=request.user, ip_address=ip)