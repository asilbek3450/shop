from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm, VerifyForm
from .services import complete_registration, find_active_verification, start_registration


SESSION_TOKEN_KEY = "pending_verification_token"


def _bot_deep_link(token):
    """Build t.me/<bot>?start=<token> link if bot username is configured."""
    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "") or ""
    bot_username = bot_username.lstrip("@")
    if not bot_username:
        return ""
    return f"https://t.me/{bot_username}?start={quote(token)}"


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            verification = start_registration(
                phone=form.cleaned_data["phone"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data.get("last_name") or "",
                password_hash=form.hashed_password(),
            )
            request.session[SESSION_TOKEN_KEY] = verification.link_token
            return redirect("accounts:verify")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "title": "Ro'yxatdan o'tish — uzshop",
            "page_key": "register",
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
def verify(request):
    if request.user.is_authenticated:
        return redirect("profile")

    token = request.session.get(SESSION_TOKEN_KEY)
    verification = find_active_verification(token) if token else None
    if not verification:
        messages.error(request, "Tasdiqlash sessiyasi topilmadi yoki muddati tugagan. Qayta ro'yxatdan o'ting.")
        return redirect("accounts:register")

    deep_link = _bot_deep_link(verification.link_token)
    error_message = None

    if request.method == "POST":
        form = VerifyForm(request.POST)
        if form.is_valid():
            user, error = complete_registration(verification, form.cleaned_data["code"])
            if user:
                request.session.pop(SESSION_TOKEN_KEY, None)
                login(request, user, backend="accounts.backends.PhoneBackend")
                messages.success(request, f"Xush kelibsiz, {user.first_name}!")
                return redirect("profile")
            error_message = error
    else:
        form = VerifyForm()

    return render(
        request,
        "accounts/verify.html",
        {
            "title": "Tasdiqlash — uzshop",
            "page_key": "verify",
            "form": form,
            "verification": verification,
            "deep_link": deep_link,
            "bot_username": getattr(settings, "TELEGRAM_BOT_USERNAME", ""),
            "error_message": error_message,
            "code_ready": bool(verification.code) and verification.contact_shared_at is not None,
        },
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.user)
            next_url = request.GET.get("next") or reverse("profile")
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "title": "Kirish — uzshop",
            "page_key": "login",
            "form": form,
        },
    )


@require_http_methods(["POST"])
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Tizimdan chiqdingiz.")
    return redirect("index")
