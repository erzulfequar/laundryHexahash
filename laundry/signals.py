from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


from .models import LoginLog, LogoutLog

def get_client_ip(request):
    """Helper to get IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    LoginLog.objects.create(user=user, ip_address=ip)



