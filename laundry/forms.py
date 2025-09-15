from django import forms
from .models import Customer, Order, Staff, Branch
from django.contrib.auth.models import User
from accounts.models import CustomUser


# ------------------- Customer Form -------------------
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@email.com'}),

        }

# ------------------- Order Form -------------------
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'weight_kg']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter weight in kg'}),
        }





class StaffForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'id_username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password'
        })
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Branch"
    )

    class Meta:
        model = Staff
        fields = []

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.created_by = kwargs.pop('created_by', None)
        super().__init__(*args, **kwargs)

        if self.organization:
            self.fields['branch'].queryset = Branch.objects.filter(organization=self.organization)

    def save(self, commit=True):
        # ✅ Create CustomUser not default User
        # Correct:
        user = CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            is_staff=True
        )

        user.organization = self.organization
        user.save()

        # ✅ Create Staff and assign org, branch, created_by
        staff = Staff(
            user=user,
            branch=self.cleaned_data['branch'],
            created_by=self.created_by,
            organization=self.organization
        )
        if commit:
            staff.save()
        return staff

from django import forms
from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['name', 'category', 'only_iron_price', 'with_wash_price', 'image','dry_clean_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'only_iron_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'with_wash_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dry_clean_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import Organization

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'address', 'logo']



from django import forms
from .models import Order, OrderItem
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['service_type', 'item_name', 'quantity']
        widgets = {
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'article': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Shirt (With Wash)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }