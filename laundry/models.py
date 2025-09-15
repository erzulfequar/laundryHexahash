from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator





class Branch(models.Model):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='branches'
    )
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, help_text="e.g., BR001, BR002")  # removed unique=True
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            # Get the highest BR code within the same organization
            last_branch = Branch.objects.filter(organization=self.organization).order_by('-id').first()
            if last_branch and last_branch.code:
                try:
                    last_number = int(last_branch.code.replace("BR", ""))
                except ValueError:
                    last_number = 0
                next_number = last_number + 1
            else:
                next_number = 1
            self.code = f"BR{next_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('organization', 'code')  # ✅ Enforce per-org uniqueness



class Customer(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    email = models.EmailField(blank=True)

    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='customers')
    branch_customer_number = models.PositiveIntegerField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.branch_customer_number and self.branch:
            last_customer = Customer.objects.filter(branch=self.branch).order_by('-branch_customer_number').first()
            self.branch_customer_number = (last_customer.branch_customer_number + 1) if last_customer else 1
        super().save(*args, **kwargs)

    def get_branch_customer_id(self):
        if self.branch and self.branch_customer_number:
            return f"BR{self.branch_customer_number:04d}"
        return ""

    def __str__(self):
        return self.name

#---------------------order-------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Online', 'Online'),
        ('Card', 'Card'),
    ]
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True)
    weight_kg = models.FloatField()
    services_items = models.TextField(
        blank=True,
        help_text="Use format: Service: Item Description × Quantity\nExample:\nIroning: Shirt (With Wash) × 2"
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    branch_order_number = models.PositiveIntegerField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.branch_order_number and self.branch:
            last_order = Order.objects.filter(branch=self.branch).order_by('-branch_order_number').first()
            self.branch_order_number = (last_order.branch_order_number + 1) if last_order else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.branch_order_number} - {self.customer.name}"
    class Meta:
        ordering = ['-created_at']

    def get_order_number(self):
        if self.branch and self.branch.code and self.branch_order_number:
            return f"{self.branch.code}-{self.branch_order_number:03d}"
        elif self.branch_order_number:
            return f"ORD-{self.branch_order_number:03d}"
        return f"ORD-{self.id or 'XXX'}"

class OrderItem(models.Model):
    SERVICE_CHOICES = [
        ('Ironing', 'Ironing'),
        ('Dryclean', 'Dryclean'),
        ('Other', 'Other'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    item_name = models.CharField(max_length=100)
    with_wash = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.service_type} - {self.item_name} × {self.quantity}"




from django.db.models import Max

class Staff(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_staff', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=10, blank=True, )

    def save(self, *args, **kwargs):
        if not self.code:
            if not self.branch:
                raise ValueError("Branch is required to generate staff code.")

            existing_codes = (
                Staff.objects.filter(branch=self.branch)
                .exclude(code__isnull=True)
                .exclude(code__exact='')
                .values_list("code", flat=True)
            )
            numbers = [
                int(c[2:]) for c in existing_codes
                if c.startswith("ST") and c[2:].isdigit()
            ]
            next_number = max(numbers, default=0) + 1
            self.code = f"ST{next_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username




class Article(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
    CATEGORY_CHOICES = [
        ('Boys', 'Boys'),
        ('Girls', 'Girls'),
        ('Kids', 'Kids'),
        ('Others', 'Others'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    only_iron_price = models.DecimalField(max_digits=6, decimal_places=2)
    with_wash_price = models.DecimalField(max_digits=6, decimal_places=2)
    dry_clean_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category})"


class OTPRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    via = models.CharField(max_length=10, choices=(("email", "Email"), ("mobile", "Mobile")))

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=1)

#--------------------organisation-----------------------------------

def generate_org_id():
    last_org = Organization.objects.order_by('-id').first()
    next_id = (last_org.id + 1) if last_org else 1
    return f"HEXA{str(next_id).zfill(3)}"


 # If you have this in a utils file

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Organization(models.Model):
    is_approved = models.BooleanField(default=False)

    name = models.CharField(max_length=255)
    address = models.TextField()

    country_code = models.CharField(
        max_length=5,
        default='+91',
        help_text="Country Code (e.g., +91)"
    )

    phone = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(r'^\d{10}$', message="Phone number must be exactly 10 digits")
        ],
        help_text="Enter 10-digit mobile number"
    )

    whatsapp = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField()
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_organizations"
    )

    org_id = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    allowed_branches = models.PositiveIntegerField(default=0)
    allowed_staff = models.PositiveIntegerField(default=0)

    # ✅ Add Plan relationship and dates
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    plan_start_date = models.DateField(null=True, blank=True)
    plan_end_date = models.DateField(null=True, blank=True)

    def is_valid(self):
        return self.plan_end_date and self.plan_end_date >= timezone.now().date()

    def days_remaining(self):
        if self.plan_end_date:
            remaining = (self.plan_end_date - timezone.now().date()).days
            return remaining if remaining > 0 else 0  # ✅ no negative values
        return 0

    def is_expired(self):
        return self.plan_end_date and self.plan_end_date < timezone.now().date()

    def save(self, *args, **kwargs):
        if not self.org_id:
            self.org_id = generate_org_id()
        super().save(*args, **kwargs)



    def __str__(self):
        return self.name

#--------Login log out Activity monitor------
class LoginLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"

class LogoutLog(models.Model):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
        logout_time = models.DateTimeField(auto_now_add=True)
        ip_address = models.GenericIPAddressField(null=True, blank=True)

        def __str__(self):
            return f"{self.user.username} - {self.logout_time}"


