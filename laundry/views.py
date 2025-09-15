from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Organization, Plan
from .forms import ArticleForm
from .models import Branch
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import Customer, Order, Staff
from .forms import StaffForm
import json
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
from dateutil.relativedelta import relativedelta
# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.db.models.functions import ExtractYear
from django.http import HttpResponseNotFound
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
User = get_user_model()
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Order, Article
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemForm


#---------landing public page-----

def landing_page(request):
    return render(request, 'public/landing.html')
#---------company register--------------

def register_company(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        whatsapp = request.POST.get('whatsapp')
        email = request.POST.get('email')
        gst_number = request.POST.get('gst_number')
        logo = request.FILES.get('logo')

        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, "organization/register.html", {
                "error": "Passwords do not match. Please try again."
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register_company')

        # ✅ Create user with is_org_admin=True and inactive until approval
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # ⛔ Not allowed to log in until approved
        user.is_staff = True    # Optional, allows admin site if needed
        user.is_org_admin = True  # ✅ Give role as OrgAdmin

        user.save()

        # ✅ Create organization and assign owner
        org = Organization.objects.create(
            name=name,
            address=address,
            phone=phone,
            whatsapp=whatsapp,
            email=email,
            gst_number=gst_number,
            logo=logo,
            created_by=user
        )

        # ✅ Link org to user
        user.organization = org
        user.save()

        return redirect("register_success")

    return render(request, "organization/register.html")



def register_success(request):
    return render(request, "organization/register_success.html")





# --------------------- LOGIN ---------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = authenticate(request, username=username, password=password)

        if user:
            if role == "owner" and hasattr(user, 'staff'):
                return render(request, 'accounts/login.html', {'error': 'This user is staff, not owner'})
            elif role == "staff" and not hasattr(user, 'staff'):
                return render(request, 'accounts/login.html', {'error': 'This user is not a staff member'})

            login(request, user)

            # ✅ Redirect based on role
            if user.is_org_admin:
                return redirect('dashboard')  # Organization admin dashboard
            else:
                return redirect('home')  # Staff dashboard

        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})

    return render(request, 'accounts/login.html')



def logout_view(request):
    logout(request)
    return redirect('login')

def plan_expired_page(request):
    return render(request, 'plan/plan_expired.html')
# --------------------- HOME ---------------------
@login_required
def home(request):
    organization = request.user.organization

    if organization.is_expired():
        messages.error(request, "🚫 Your plan has expired. Please renew to continue.")
        return render(request, 'plan/plan_expired.html')

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")


        if name and phone:
            existing = Customer.objects.filter(name=name, email=email, organization=request.user.organization ).first()
            if existing:
                return JsonResponse({
                    'status': 'success',
                    'id': existing.id,
                    'name': existing.name,
                    'phone': existing.phone,
                    'email': existing.email,


                })

            try:
                new_customer = Customer.objects.create(
                    name=name,
                    phone=phone,
                    email=email,
                    branch=request.user.staff.branch if hasattr(request.user, 'staff') else None,
                    organization = request.user.organization
                )

                return JsonResponse({
                    'status': 'success',
                    'id': new_customer.id,
                    'name': new_customer.name,
                    'phone': new_customer.phone,
                    'email': new_customer.email
                })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        else:
            return JsonResponse({'status': 'error', 'message': 'Missing fields'})
    if hasattr(request.user, 'staff'):
        customers = Customer.objects.filter(branch=request.user.staff.branch,organization=request.user.organization).order_by('-id')
    else:
        customers = Customer.objects.filter(
            organization=request.user.organization
        ).order_by('-id')

    articles = Article.objects.filter(organization=request.user.organization)  # 🔹 Add this line
    today_date = timezone.now().strftime("%d-%m-%Y")
    current_time = timezone.now().strftime("%I:%M %p")
    invoice_number = f"{Customer.objects.filter(organization=request.user.organization).count() + 1:04d}"

    return render(request, 'laundry/home.html', {
        'customers': customers,
        'articles': articles,  # 🔹 Pass to template
        'today_date': today_date,
        'current_time': current_time,
        'invoice_number': invoice_number,
        'categories': ['Boys', 'Girls', 'Kids', 'Others']

    })


# --------------------- DASHBOARD ---------------------
@login_required

def dashboard(request):
    user = request.user
    today = timezone.now().date()
    branches = Branch.objects.filter(created_by__organization=request.user.organization)

    selected_branch_id = request.GET.get("branch_id")
    # ✅ Branch Filter Start
    if getattr(user, "is_org_admin", False):
        branches = Branch.objects.filter(organization=user.organization)

        if selected_branch_id and selected_branch_id != "all":
            orders = Order.objects.filter(branch_id=selected_branch_id, organization=user.organization)
            customer_qs = Customer.objects.filter(branch_id=selected_branch_id, organization=user.organization)
        else:
            orders = Order.objects.filter(organization=user.organization)
            customer_qs = Customer.objects.filter(organization=user.organization)

    else:
        try:
            staff = Staff.objects.get(user=user)
            branches = Branch.objects.filter(id=staff.branch.id)
            orders = Order.objects.filter(branch=staff.branch, organization=user.organization)
            customer_qs = Customer.objects.filter(branch=staff.branch, organization=user.organization)
        except Staff.DoesNotExist:
            return HttpResponse("Unauthorized", status=401)

    # ✅ Branch Filter End

    total_orders = orders.count()
    in_progress_orders = orders.exclude(status="Completed").count()
    total_completed_orders = orders.filter(status="Completed").count()
    lifetime_revenue = orders.aggregate(total=Sum("total_amount"))["total"] or 0

    todays_orders = orders.filter(created_at__date=today).count()
    pending_orders = orders.filter(created_at__date=today, status="Pending").count()
    completed_orders = orders.filter(created_at__date=today, status="Completed").count()
    total_revenue = orders.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"] or 0

    # ✅ Apply branch filter to top customers section


    top_customers = customer_qs.annotate(
        total_orders=Count("order"),
        total_spent=Sum("order__total_amount")
    ).order_by("-total_spent")[:10]

    # ✅ Weekly Revenue
    weekly_labels, weekly_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        total = orders.filter(created_at__date=day).aggregate(sum=Sum("total_amount"))["sum"] or 0
        weekly_labels.append(day.strftime('%a'))
        weekly_data.append(float(total))

    # ✅ Monthly Revenue
    monthly_labels, monthly_data = [], []
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        total = orders.filter(created_at__date__gte=month_start, created_at__date__lt=month_end).aggregate(
            sum=Sum("total_amount"))["sum"] or 0
        monthly_labels.append(month_start.strftime('%b'))
        monthly_data.append(float(total))

    # ✅ Yearly Revenue
    yearly_labels, yearly_data = [], []
    for y in range(today.year - 2, today.year + 1):
        total = orders.filter(created_at__year=y).aggregate(sum=Sum("total_amount"))["sum"] or 0
        yearly_labels.append(str(y))
        yearly_data.append(float(total))

    # ✅ Weekly Order Count
    weekly_order_labels, weekly_order_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = orders.filter(created_at__date=day).count()
        weekly_order_labels.append(day.strftime('%a'))
        weekly_order_data.append(count)

    # ✅ Monthly Order Count
    monthly_order_labels, monthly_order_data = [], []
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        count = orders.filter(created_at__date__gte=month_start, created_at__date__lt=month_end).count()
        monthly_order_labels.append(month_start.strftime('%b'))
        monthly_order_data.append(count)

    # ✅ Yearly Order Count
    yearly_order_labels, yearly_order_data = [], []
    for y in range(today.year - 2, today.year + 1):
        count = orders.filter(created_at__year=y).count()
        yearly_order_labels.append(str(y))
        yearly_order_data.append(count)
    # Build data dictionaries for tables
    weekly_orders_data = dict(zip(weekly_order_labels, weekly_order_data))
    monthly_orders_data = dict(zip(monthly_order_labels, monthly_order_data))
    yearly_orders_data = dict(zip(yearly_order_labels, yearly_order_data))
    weekly_orders_total = sum(weekly_order_data)
    monthly_orders_total = sum(monthly_order_data)
    yearly_orders_total = sum(yearly_order_data)
    charts_data = [
        {
            "id": "weekly",
            "title": "Weekly Revenue",
            "labels": weekly_labels,
            "data": weekly_data
        },
        {
            "id": "monthly",
            "title": "Monthly Revenue",
            "labels": monthly_labels,
            "data": monthly_data
        },
        {
            "id": "yearly",
            "title": "Yearly Revenue",
            "labels": yearly_labels,
            "data": yearly_data

        }
    ]




    return render(request, "laundry/dashboard.html",
{
        "total_orders": total_orders,
        "in_progress_orders": in_progress_orders,
        "total_completed_orders": total_completed_orders,
        "lifetime_revenue": lifetime_revenue,
        "todays_orders": todays_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_revenue": total_revenue,
        "top_customers": top_customers,
        "weekly_labels": json.dumps(weekly_labels),
        "weekly_data": json.dumps(weekly_data),
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_data": json.dumps(monthly_data),
        "yearly_labels": json.dumps(yearly_labels),
        "yearly_data": json.dumps(yearly_data),
        "weekly_order_labels": json.dumps(weekly_order_labels),
        "weekly_order_data": json.dumps(weekly_order_data),
        "monthly_order_labels": json.dumps(monthly_order_labels),
        "monthly_order_data": json.dumps(monthly_order_data),
        "yearly_order_labels": json.dumps(yearly_order_labels),
        "yearly_order_data": json.dumps(yearly_order_data),
        "branches": branches,
        "selected_branch_id": selected_branch_id,
        "charts_data": charts_data,
        "weekly_orders_data": weekly_orders_data,
        "monthly_orders_data": monthly_orders_data,
        "yearly_orders_data": yearly_orders_data,


    })



# --------------------- STAFF MANAGEMENT ---------------------
def is_owner(user):
    return not hasattr(user, 'staff')

@login_required
@user_passes_test(is_owner)
def staff_list(request):
    # ✅ Step 1: Branches and selected branch from URL
    branches = Branch.objects.filter(organization=request.user.organization)

    selected_branch_id = request.GET.get("branch_id")

    # ✅ Step 2: Filter logic based on selected_branch_id
    if selected_branch_id and selected_branch_id != "all":
        staffs = Staff.objects.select_related('user').filter(branch_id=selected_branch_id, organization=request.user.organization).order_by('-created_at')
    else:
        staffs = Staff.objects.select_related('user').filter(
            organization=request.user.organization
        ).order_by('-created_at')

    # ✅ Step 3: Return context including filter data
    return render(request, 'staff/list.html', {
        'staffs': staffs,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })

@login_required
@user_passes_test(is_owner)
def add_staff(request):
    organization = request.user.organization  # ✅ Get the current org from logged-in user

    # Count existing staff for this organization
    staff_count = Staff.objects.filter(organization=organization).count()

    if organization.allowed_staff is not None and staff_count >= organization.allowed_staff:
        messages.error(request, "🚫 Staff limit reached for your current plan.")
        return redirect('staff_list')  # or wherever your staff list page is


    if request.method == 'POST':
        form = StaffForm(request.POST, organization=request.user.organization, created_by=request.user)
        if form.is_valid():
            try:
                form.save()
                return redirect('staff_list')
            except Exception as e:
                form.add_error(None, f"Error: {e}")
    else:
        form = StaffForm(organization=request.user.organization, created_by=request.user)

    branches = Branch.objects.filter(organization=request.user.organization)
    return render(request, 'staff/add.html', {'form': form, 'branches': branches})





# --------------------- INVOICES ---------------------
@login_required
def invoice_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    selected_branch_id = request.GET.get('branch_id')  # ✅ Step 1: Get selected branch
    branches = Branch.objects.filter(organization=request.user.organization)


    # ✅ Step 3: Apply branch filtering
    if hasattr(request.user, 'staff'):
        # Staff sees only their own branch
        invoices = Order.objects.select_related('customer').filter(branch=request.user.staff.branch)
    else:
        # Admin can filter by branch
        if selected_branch_id and selected_branch_id != "all":
            invoices = Order.objects.select_related('customer').filter(branch_id=selected_branch_id,organization=request.user.organization)
        else:
            invoices = Order.objects.select_related('customer').filter(organization=request.user.organization)

    # ✅ Step 4: Apply search filter
    if query:
        invoices = invoices.filter(
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(id__icontains=query)
        )

    # ✅ Step 5: Apply status filter
    if status_filter == 'paid':
        invoices = invoices.filter(is_paid=True)
    elif status_filter == 'pending':
        invoices = invoices.filter(is_paid=False)

    # ✅ Step 6: Send all context to template
    return render(request, 'invoices/list.html', {
        'invoices': invoices.order_by('-created_at'),
        'query': query,
        'status_filter': status_filter,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })








#------------invoice view----------
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Order, Article



@login_required



def invoice_view(request, order_id):
    order = get_object_or_404(Order.objects.select_related("branch"), id=order_id)

    # 🛡️ Check access permissions
    if not request.user.is_superuser and order.organization != request.user.organization:
        return HttpResponse("Unauthorized", status=401)

    customer = order.customer
    order_items = OrderItem.objects.filter(order=order)
    items = []

    # ✅ Check if washing is applicable
    has_washing = any(item.with_wash for item in order_items)
    show_washing_row = order.weight_kg and order.weight_kg > 0 and has_washing

    # if show_washing_row:
    #     wash_rate = 45 if order.weight_kg > 2.99 else 50
    #     wash_amount = order.weight_kg * wash_rate
    #     items.append({
    #         "description": "Washing 234",
    #         "qty": f"{order.weight_kg} kg",
    #         "rate": wash_rate,
    #         "amount": wash_amount
    #     })

    # ✅ Add individual order items
    for item in order_items:
        article_name = item.item_name
        with_wash = item.with_wash
        qty = item.quantity
        service_type = item.service_type

        # Try exact match first, then partial match
        article = (
            Article.objects.filter(name__iexact=article_name).first()
            or Article.objects.filter(name__icontains=article_name.split('(')[0].strip()).first()
        )

        if not article:
            print(f"❌ Article not found: {article_name}")
            rate = 0.0
            desc = f"{article_name} (Unknown)"
        else:
            if service_type == "Dryclean":
                rate = float(article.dry_clean_price or 0)
                desc = f"{article.name} "
            elif with_wash:
                rate = float(article.with_wash_price or 0)
                desc = f"{article.name} (With Wash)"
            else:
                rate = float(article.only_iron_price or 0)
                desc = f'{article.name} <small>(Without Wash)</small>'


        amount = qty * rate
        items.append({
            "description": desc,
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "service_type": service_type,
        })

    context = {
        'order': order,
        'customer': customer,
        'items': items,
        'weight': order.weight_kg,
    }

    return render(request, 'invoices/invoice_view.html', context)



















@require_POST
@login_required
def update_invoice_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_superuser and order.organization != request.user.organization:
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    is_paid = request.POST.get('is_paid')
    if is_paid == 'paid':
        order.is_paid = True
    elif is_paid == 'pending':
        order.is_paid = False
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status'})
    order.save()
    return JsonResponse({'success': True})

from .models import Article


# --------------------- CUSTOMERS ---------------------
@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    selected_branch_id = request.GET.get('branch_id', 'all')
    user = request.user

    # Get branches of current user's organization
    if hasattr(user, 'staff'):
        # Staff: only their branch
        customers = Customer.objects.filter(branch=user.staff.branch, organization=user.organization)
        branches = Branch.objects.filter(id=user.staff.branch.id)
    else:
        # Org admin
        branches = Branch.objects.filter(organization=user.organization)
        if selected_branch_id != "all":
            customers = Customer.objects.filter(branch_id=selected_branch_id, organization=user.organization)
        else:
            customers = Customer.objects.filter(organization=user.organization)

    # Search filter
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'customers/list.html', {
        'customers': customers,
        'query': query,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })



@login_required
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(customer=customer, organization=request.user.organization).order_by('-created_at')
    return render(request, 'customers/detail.html', {
        'customer': customer,
        'orders': orders
    })


# --------------------- ORDERS ---------------------
@login_required
def order_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    selected_branch_id = request.GET.get('branch_id')  # ✅ Step 1: Get selected branch
    branches = Branch.objects.filter(organization=request.user.organization)


    # ✅ Step 3: Branch filter logic
    if hasattr(request.user, 'staff'):
        orders = Order.objects.select_related('customer').filter(branch=request.user.staff.branch,organization=request.user.organization)
    else:
        if selected_branch_id and selected_branch_id != "all":
            orders = Order.objects.select_related('customer').filter(branch_id=selected_branch_id,organization=request.user.organization)
        else:
            orders = Order.objects.select_related('customer').filter(organization=request.user.organization)


    # ✅ Step 4: Search filter
    if query:
        orders = orders.filter(
            Q(id__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query)
        )

    # ✅ Step 5: Status filter
    if status_filter:
        orders = orders.filter(status=status_filter)

    # ✅ Step 6: Render with all filters
    return render(request, 'orders/list.html', {
        'orders': orders.order_by('-created_at'),
        'query': query,
        'status_filter': status_filter,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })

from .models import OrderItem
@require_POST
@login_required
 # make sure this is imported



def save_order(request):
    try:
        data = json.loads(request.body)
        print("🟡 Received order data:", data)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    try:
        customer_id = data.get('customer_id')
        weight = data.get('weight')
        ironing_items = data.get('ironing_items', [])
        dryclean_items = data.get('dryclean_items', [])
        total_amount = data.get('total_amount')
        status = data.get('status', 'Pending')

        customer = Customer.objects.get(id=customer_id)

        # ✅ Build the service_items summary string for display
        service_summary_lines = []

        for item in ironing_items:
            article = item.get('article', '')
            qty = item.get('qty', 1)
            with_wash = item.get('with_wash', False)

            if article.strip().lower() == "washing":
                continue  # 🚫 skip adding Washing to summary

            label = f"{article} {'(With Wash)' if with_wash else '(Without Wash)'} × {qty}"
            service_summary_lines.append(f"Ironing: {label}")

        for item in dryclean_items:
            article = item.get('article', '')
            qty = item.get('qty', 1)
            label = f"{article} × {qty}"
            service_summary_lines.append(f"Dry Clean: {label}")

        services_items_text = "\n".join(service_summary_lines)

        # ✅ Create Order
        order = Order.objects.create(
            customer=customer,
            weight_kg=weight,
            services_items=services_items_text,
            total_amount=total_amount,
            status=status,
            branch=request.user.staff.branch if hasattr(request.user, 'staff') else None,
            organization=request.user.organization
        )

        # ✅ Create Ironing OrderItems (excluding washing)
        for item in ironing_items:
            article = item.get('article', '').strip()

            if article.lower() == "washing":
                continue  # 🚫 skip saving Washing

            OrderItem.objects.create(
                order=order,
                service_type='Ironing',
                item_name=article,
                with_wash=item.get('with_wash', False),
                quantity=item.get('qty', 1)
            )

        # ✅ Create Dryclean OrderItems
        for item in dryclean_items:
            OrderItem.objects.create(
                order=order,
                service_type='Dryclean',
                item_name=item.get('article'),
                with_wash=False,
                quantity=item.get('qty', 1)
            )

        return JsonResponse({'success': True, 'order_id': order.id})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})






#----------new add--------
@require_POST
@login_required
def ajax_update_order_status(request, order_id):
    try:
        data = json.loads(request.body)
        new_status = data.get('status')

        if not new_status:
            return JsonResponse({'success': False, 'error': 'Missing status'})

        if new_status not in ['Pending', 'Completed']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})

        # Always filter by organization
        order = get_object_or_404(Order, id=order_id, organization=request.user.organization)

        # Extra check: staff can update only their branch
        if hasattr(request.user, 'staff') and order.branch != request.user.staff.branch:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})

        order.status = new_status
        order.save()
        return JsonResponse({'success': True})

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})







# --------------------- USER PROFILE ---------------------
@login_required
def edit_profile(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        if new_username:
            request.user.username = new_username
            request.user.save()
            messages.success(request, 'Username updated successfully.')
            return redirect('edit_profile')
    return render(request, 'accounts/edit_profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('change_password')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
#--------------barnches---------------



def is_owner(user):
    return not hasattr(user, 'staff')

#-------Branches----------------
@login_required
@user_passes_test(is_owner)
def branch_list(request):
    branches = Branch.objects.filter(organization=request.user.organization)  # ✅ Scoped to org
    return render(request, 'branches/branch_list.html', {'branches': branches})

# ✅ View: Add Branch (automatically assign to organization)



 # Make sure this is imported


from django.shortcuts import redirect

@login_required
@user_passes_test(is_owner)
def branch_add(request):
    organization = request.user.organization

    # ✅ Branch limit check before POST
    branch_count = Branch.objects.filter(organization=organization).count()
    if organization.allowed_branches is not None and branch_count >= organization.allowed_branches:
        messages.error(request, "🚫 Branch limit reached for your current plan.")
        return redirect('branch_list')  # 🔁 Redirect after showing message to prevent duplicates

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")

        if name:
            Branch.objects.create(
                name=name,
                address=address,
                phone=phone,
                organization=organization

            )
            messages.success(request, "✅ Branch created successfully!")
            return redirect('branch_list')

    return render(request, 'branches/branch_add.html')





#----------------Article---------------


# Add New Article
@login_required
def article_add(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.organization = request.user.organization
            article.save()
            return redirect('article_list')
    else:
        form = ArticleForm()
    return render(request, 'articles/article_add.html', {'form': form})

# List All Articles
def article_list(request):
    category = request.GET.get('category')

    articles = Article.objects.filter(organization=request.user.organization)

    if category and category != 'All':
        articles = articles.filter(category=category)  # ✅ continue filtering from org-specific queryset

    return render(request, 'articles/article_list.html', {
        'articles': articles,
        'selected_category': category or 'All',
    })


def article_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if not request.user.is_superuser and article.organization != request.user.organization:
        return HttpResponse("Unauthorized", status=401)  # ✅ Prevent cross-org access

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            return redirect('article_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'articles/article_add.html', {'form': form, 'edit_mode': True})

# Delete Article
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if not request.user.is_superuser and article.organization != request.user.organization:
        return HttpResponse("Unauthorized", status=401)

    article.delete()
    return redirect('article_list')


#forget password--------------







def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        users = User.objects.filter(email=email)

        if users.exists():
            for user in users:
                subject = 'Password Reset Requested'
                email_template_name = 'Accounts/password_reset_email.txt'  # You must create this!
                context = {
                    'email': user.email,
                    'domain': request.get_host(),
                    'site_name': 'Laundry POS',
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'user': user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        order.status = new_status
        order.save()
        return redirect('order_list')  # or wherever you want to go after update
    return render(request, 'orders/update_status.html', {'order': order})

#dashboard download---------------
@login_required

def export_dashboard_excel(request):
    today = now().date()
    selected_branch_id = request.GET.get("branch_id")

    if request.user.is_superuser:
        if selected_branch_id and selected_branch_id != "all":
            orders = Order.objects.filter(branch_id=selected_branch_id)
        else:
            orders = Order.objects.all()
    else:
        try:
            staff = Staff.objects.get(user=request.user)
            orders = Order.objects.filter(branch=staff.branch)
        except Staff.DoesNotExist:
            return HttpResponse("Unauthorized", status=401)

    # Time ranges
    three_months_ago = today - relativedelta(months=3)
    six_months_ago = today - relativedelta(months=6)
    year_start = today.replace(month=1, day=1)

    # Summary Sheet Data
    summary_data = [
        ["Metric", "Value"],
        ["Total Orders (All Time)", orders.count()],
        ["Total Revenue (All Time)", orders.aggregate(total=Sum("total_amount"))["total"] or 0],
        ["Orders (Last 3 Months)", orders.filter(created_at__date__gte=three_months_ago).count()],
        ["Revenue (Last 3 Months)", orders.filter(created_at__date__gte=three_months_ago).aggregate(total=Sum("total_amount"))["total"] or 0],
        ["Orders (Last 6 Months)", orders.filter(created_at__date__gte=six_months_ago).count()],
        ["Revenue (Last 6 Months)", orders.filter(created_at__date__gte=six_months_ago).aggregate(total=Sum("total_amount"))["total"] or 0],
        ["Orders (This Year)", orders.filter(created_at__date__gte=year_start).count()],
        ["Revenue (This Year)", orders.filter(created_at__date__gte=year_start).aggregate(total=Sum("total_amount"))["total"] or 0],
    ]

    # Year-wise Aggregation
    year_data_qs = orders.annotate(year=ExtractYear("created_at")).values("year").order_by("-year").distinct()
    year_data = [["Year", "Total Orders", "Total Revenue"]]

    for entry in year_data_qs:
        year = entry["year"]
        year_orders = orders.filter(created_at__year=year)
        total_orders = year_orders.count()
        total_revenue = year_orders.aggregate(total=Sum("total_amount"))["total"] or 0
        year_data.append([year, total_orders, total_revenue])

    # Create Workbook
    wb = Workbook()

    # Summary Sheet
    summary_ws = wb.active
    summary_ws.title = "Dashboard Summary"

    style_header(summary_ws, summary_data[0])
    fill_data(summary_ws, summary_data[1:])

    # Yearly Breakdown Sheet
    yearly_ws = wb.create_sheet(title="Yearly Report")
    style_header(yearly_ws, year_data[0])
    fill_data(yearly_ws, year_data[1:])

    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"dashboard_summary_{today}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response


# === Utilities ===
def style_header(ws, header_row):
    """Apply styles to header row"""
    bold_font = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="4F81BD")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    align = Alignment(horizontal="center", vertical="center")

    for col_num, header in enumerate(header_row, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = bold_font
        cell.fill = fill
        cell.border = border
        cell.alignment = align


def fill_data(ws, data_rows):
    """Fill data rows with borders and alignment"""
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    align = Alignment(horizontal="center", vertical="center")

    for row_idx, row_data in enumerate(data_rows, start=2):
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border
            cell.alignment = align

    # Auto-fit column width
    for col in ws.columns:
        max_length = max((len(str(cell.value)) if cell.value else 0) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 4


from .models import Organization

# ✅ Check if user is superadmin

def superadmin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You are not authorized to view this page.")
        return HttpResponseForbidden("Please login as superadmin to access this page.")
    return _wrapped_view

@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin_dashboard(request):
    # Base queryset
    organizations = Organization.objects.all().order_by("-created_at")

    # Apply search filter
    query = request.GET.get("q")
    if query:
        organizations = organizations.filter(name__icontains=query)

    # Apply pending filter
    filter_pending = request.GET.get("filter") == "pending"
    if filter_pending:
        organizations = organizations.filter(is_approved=False)

    # Count stats (not affected by filtering)
    total = Organization.objects.count()
    approved = Organization.objects.filter(is_approved=True).count()
    pending = Organization.objects.filter(is_approved=False).count()

    return render(request, "superadmin/dashboard.html", {
        "organizations": organizations,
        "total": total,
        "approved": approved,
        "pending": pending,
        "search_query": query or "",  # Optional: to show in input field
    })



def approve_organization(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    org.is_approved = True
    org.save()

    # ✅ Activate the associated user account
    if org.created_by:
        org.created_by.is_active = True
        org.created_by.save()

    return redirect('superadmin_dashboard')

@superadmin_required
def reject_organization(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    org.delete()
    return redirect('superadmin_dashboard')


def export_organizations_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Status', 'Created At'])

    for org in Organization.objects.all():
        writer.writerow([
            org.name,
            org.email,
            org.phone,
            'Approved' if org.is_approved else 'Pending',
            org.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response

from datetime import date

def view_organization(request, org_id=None):
    organization = None
    days_remaining = None

    if org_id:
        try:
            organization = Organization.objects.get(id=org_id)
            # ✅ calculate remaining days if plan_end_date exists
            if organization.plan_end_date:
                days_remaining = (organization.plan_end_date - date.today()).days
        except Organization.DoesNotExist:
            organization = None

    all_organizations = Organization.objects.all().order_by("name")

    return render(request, "superadmin/organization_detail.html", {
        "organization": organization,
        "all_organizations": all_organizations,
        "organizations": all_organizations,
        "days_remaining": days_remaining,
    })

def organization_manage(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    plan = org.plan if org.plan else None
    return render(request, 'superadmin/organization_manage.html', {
        'org': org,
        'plan': plan,
    })

# 1️⃣ Show all organizations (listing page)
def manage_users(request):
    all_orgs = Organization.objects.all().order_by('-created_at')  # Recent first
    return render(request, "superadmin/manage_users.html", {
        "organizations": all_orgs  # Use "organizations" instead of "all_organizations"
    })


# 2️⃣ View/manage a single organization's detail
def manage_user_detail(request, org_id):
    org = get_object_or_404(Organization, id=org_id)

    days_remaining = None
    if org.plan_end_date:
        days_remaining = (org.plan_end_date - timezone.now().date()).days
    org.days_remaining = days_remaining

    plans = Plan.objects.all()
    organizations = Organization.objects.all().order_by("name")  # ✅ correct key

    return render(request, "superadmin/manage_user_detail.html", {
        "organization": org,
        "plans": plans,
        "organizations": organizations,  # ✅ required by sidebar
    })



# 3️⃣ Assign or update organization plan





from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotFound
from datetime import datetime
from .models import Organization, Plan  # Ensure Plan is imported

def assign_org_limits(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)

    if request.method == "POST":
        branches = request.POST.get("branches")
        staff = request.POST.get("staff")
        start_str = request.POST.get("start")
        end_str = request.POST.get("end")
        plan_id = request.POST.get("plan")

        if branches:
            organization.allowed_branches = int(branches)
        if staff:
            organization.allowed_staff = int(staff)

        # ✅ Only update dates if non-empty, else keep existing
        try:
            if start_str:
                organization.plan_start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            # else: keep existing
            if end_str:
                organization.plan_end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            # else: keep existing
        except ValueError:
            return HttpResponseNotFound("Invalid date format.")

        # ✅ Optional plan update
        if plan_id:
            try:
                plan = Plan.objects.get(id=plan_id)
                organization.plan = plan
            except Plan.DoesNotExist:
                return HttpResponseNotFound("Plan not found.")

        organization.save()

    return render(request, "superadmin/manage_user_detail.html", {
        "organization": organization,
        "plan": organization.plan if organization.plan else None,
        "organizations": organization,
    })




#----------login monitor-----------
from django.shortcuts import render, get_object_or_404
from .models import LoginLog, LogoutLog
from django.contrib.auth import get_user_model

User = get_user_model()

def login_logout_history(request):
    # List all organization admin users
    orgadmins = User.objects.filter(is_org_admin=True)
    return render(request, 'superadmin/login_history.html', {
        'orgadmins': orgadmins
    })


def orgadmin_logs(request, admin_id):
    # Show logs for a specific organization admin
    orgadmin = get_object_or_404(User, id=admin_id, is_org_admin=True)
    login_logs = LoginLog.objects.filter(user=orgadmin).order_by('-login_time')
    logout_logs = LogoutLog.objects.filter(user=orgadmin)

    logs = []
    for login in login_logs:
        logout = logout_logs.filter(user=orgadmin, logout_time__gt=login.login_time).order_by('logout_time').first()
        logs.append({
            'login_time': login.login_time,
            'logout_time': logout.logout_time if logout else None,
            'ip_address': login.ip_address,
        })

    return render(request, 'superadmin/orgadmin_logs.html', {
        'orgadmin': orgadmin,
        'logs': logs,
    })
#--------PLan-------------


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date
from .models import Branch, Staff  # adjust this if needed

@login_required
def org_my_plan(request):
    organization = request.user.organization  # assuming OrgAdmin is linked via OneToOneField

    start_date = organization.plan_start_date
    end_date = organization.plan_end_date
    branches_allowed = organization.allowed_branches or 0
    staff_allowed = organization.allowed_staff or 0

    remaining_days = (end_date - date.today()).days if end_date else None

    # ➕ Get usage
    branches_used = Branch.objects.filter(organization=organization).count()
    staff_used = Staff.objects.filter(organization=organization).count()

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'remaining_days': remaining_days,
        'branches_allowed': branches_allowed,
        'staff_allowed': staff_allowed,
        'branches_used': branches_used,
        'staff_used': staff_used,
    }
    return render(request, 'plan/my_plan.html', context)

#----------superadmin login page--------------
# views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden

def superadmin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('superadmin_dashboard')
        else:
            return render(request, 'superadmin/login.html', {'error': 'Invalid credentials'})

    return render(request, 'superadmin/login.html')
from django.contrib.auth import logout
from django.shortcuts import redirect

def superadmin_logout_view(request):
    logout(request)
    return redirect('superadmin_login')




