from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import export_dashboard_excel
from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import login_logout_history, orgadmin_logs
from .views import superadmin_login_view, superadmin_dashboard

urlpatterns = [

     path('', views.landing_page, name='landing_page'),
     path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Customers
    path('customers/', views.customer_list, name='customers'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),

    # Orders
    path('save-order/', views.save_order, name='save_order'),
    path('orders/', views.order_list, name='order_list'),

    path('orders/update-status/<int:order_id>/', views.ajax_update_order_status, name='ajax_update_order_status'),




    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/update-status/<int:order_id>/', views.update_invoice_status, name='update_invoice_status'),
    path('invoices/<int:order_id>/', views.invoice_view, name='invoice_view'),


    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.add_staff, name='add_staff'),

    # Profile----------------------------------------------

    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    #branches----------------------------------------------------

    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.branch_add, name='branch_add'),

    #articles---------------------------------------------------------------

    path('articles/', views.article_list, name='article_list'),
    path('articles/add/', views.article_add, name='article_add'),
    path('articles/edit/<int:article_id>/', views.article_edit, name='article_edit'),
    path('articles/delete/<int:article_id>/', views.article_delete, name='article_delete'),

#reset password
# urls.py

    path('accounts/forgot_password/', views.forgot_password, name='forgot_password'),


    path('export-dashboard-excel/', export_dashboard_excel, name='export_dashboard_excel'),

#---register
                  path('register-company/', views.register_company, name='register_company'),
path("register-success/", views.register_success, name="register_success"),

  # ✅ SuperAdmin URLs
                  path('superadmin_dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),

                  path('approve_organization/<int:org_id>/', views.approve_organization, name='approve_organization'),
                  path('reject_organization/<int:org_id>/', views.reject_organization, name='reject_organization'),
                  path('export_organizations_csv/', views.export_organizations_csv, name='export_organizations_csv'),
                  path("organization/", views.view_organization, name="organization_list"),
                  path("organization/<int:org_id>/", views.view_organization, name="view_organization"),

#manage user
                  path("manage-users/", views.manage_users, name="manage_users"),
                  path("manage-users/<int:org_id>/", views.manage_user_detail, name="manage_user_detail"),
                  path("assign-org/<int:org_id>/", views.assign_org_limits, name="assign_org_limits"),





    path('login-history/', login_logout_history, name='login_logout_history'),
    path('logs/<int:admin_id>/', orgadmin_logs, name='orgadmin_logs'),

    #plan-------------
path('my-plan/', views.org_my_plan, name='org_my_plan'),
path('plan-expired/',views.plan_expired_page, name='plan_expired_page'),

#---superadmin---
                  path('superadmin/login/', superadmin_login_view, name='superadmin_login'),
                  path('superadmin/dashboard/', superadmin_dashboard, name='superadmin_dashboard'),


path('superadmin/logout/', views.superadmin_logout_view, name='superadmin_logout'),


              ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
