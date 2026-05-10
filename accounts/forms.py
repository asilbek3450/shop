from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password

from .utils import normalize_phone

User = get_user_model()


class PhoneField(forms.CharField):
    def clean(self, value):
        value = super().clean(value)
        normalized = normalize_phone(value)
        if not normalized:
            raise forms.ValidationError("Telefon raqamni to'g'ri formatda kiriting (masalan +998901234567)")
        return normalized


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=80, label="Ism")
    last_name = forms.CharField(max_length=80, required=False, label="Familiya")
    phone = PhoneField(label="Telefon raqam", help_text="Telegramdagi raqamingizni kiriting")
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, label="Parol")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Parolni tasdiqlash")

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu raqam ro'yxatdan o'tgan. Kiring yoki parolni tiklang.")
        return phone

    def clean(self):
        data = super().clean()
        password = data.get("password")
        confirm = data.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Parollar mos emas")
        if password:
            try:
                validate_password(password)
            except forms.ValidationError as e:
                self.add_error("password", e)
        return data

    def hashed_password(self):
        return make_password(self.cleaned_data["password"])


class LoginForm(forms.Form):
    phone = PhoneField(label="Telefon raqam")
    password = forms.CharField(widget=forms.PasswordInput, label="Parol")

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        data = super().clean()
        phone = data.get("phone")
        password = data.get("password")
        if phone and password:
            user = authenticate(self.request, phone=phone, password=password)
            if user is None:
                raise forms.ValidationError("Telefon yoki parol noto'g'ri")
            if not user.is_active:
                raise forms.ValidationError("Foydalanuvchi faol emas")
            self.user = user
        return data


class VerifyForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=6, label="Tasdiqlash kodi")

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return code
