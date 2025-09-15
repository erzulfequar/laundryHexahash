from .models import Organization

def all_organizations(request):
    return {
        'all_organizations': Organization.objects.all().order_by("name")
    }
def org_context(request):
    if request.user.is_authenticated and hasattr(request.user, 'organization'):
        return {
            'organization': request.user.organization
        }
    return {}