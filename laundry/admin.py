from django.contrib import admin
from .models import Staff, Branch, Customer, Article, Order
from .models import Organization


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'branch', 'total_amount', 'created_at']
    list_filter = ['branch', 'status']
    search_fields = ['customer__name', 'customer__phone']

admin.site.register(Branch)
admin.site.register(Staff)
admin.site.register(Customer)
admin.site.register(Article)
admin.site.register(Order, OrderAdmin)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    search_fields = ['name', 'email']

# Register your models here.
