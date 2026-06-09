import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["tenant", "name"]]

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("role") != User.Role.MANAGER:
            extra_fields.setdefault("role", User.Role.MANAGER)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=16, choices=Role.choices)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        pass

    def __str__(self):
        return self.email


class ModulePermission(models.Model):
    class Module(models.TextChoices):
        DASHBOARD = "dashboard", "Dashboard"
        CLIENTS = "clients", "Clients"
        REVIEWS = "reviews", "Reviews"
        ANALYTICS = "analytics", "Analytics"
        SETTINGS = "settings", "Settings"
        AGENT = "agent", "Agent"

    class Level(models.TextChoices):
        NONE = "none", "None"
        VIEW = "view", "View"
        EDIT = "edit", "Edit"
        RUN = "run", "Run"
        USE = "use", "Use"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="module_permissions")
    module = models.CharField(max_length=32, choices=Module.choices)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.NONE)

    class Meta:
        unique_together = [["user", "module"]]

    def __str__(self):
        return f"{self.user.email}:{self.module}={self.level}"
