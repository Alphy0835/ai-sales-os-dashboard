import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.models import User

logger = logging.getLogger(__name__)


def build_reset_url(uid: str, token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/reset-password?uid={uid}&token={token}"


def encode_uid(user: User) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def make_reset_token(user: User) -> str:
    return default_token_generator.make_token(user)


def send_password_reset_email(user: User) -> None:
    uid = encode_uid(user)
    token = make_reset_token(user)
    reset_url = build_reset_url(uid, token)
    subject = "Сброс пароля — AI Sales OS"
    message = (
        "Перейдите по ссылке для сброса пароля:\n\n"
        f"{reset_url}\n\n"
        "Ссылка действительна ограниченное время."
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Password reset email failed for %s", user.email)
        return
    if settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
        logger.info("Password reset link for %s: %s", user.email, reset_url)


def revoke_user_sessions(user: User) -> None:
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)


def resolve_user_for_reset(*, uid: str | None = None, email: str | None = None) -> User | None:
    if uid:
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            return User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
    if email:
        return User.objects.filter(email__iexact=email.strip().lower(), is_active=True).first()
    return None


def reset_password(user: User, token: str, new_password: str) -> bool:
    if not default_token_generator.check_token(user, token):
        return False
    user.set_password(new_password)
    user.save(update_fields=["password"])
    revoke_user_sessions(user)
    return True
