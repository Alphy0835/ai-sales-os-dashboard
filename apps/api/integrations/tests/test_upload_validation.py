from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ModulePermission, Tenant, User, Workspace


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UploadValidationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Upload Co", slug="upload-test")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")
        self.employee = User.objects.create_user(
            email="emp@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        for module in ModulePermission.Module.values:
            ModulePermission.objects.update_or_create(
                user=self.employee,
                module=module,
                defaults={
                    "level": ModulePermission.Level.VIEW if module == ModulePermission.Module.DASHBOARD else ModulePermission.Level.NONE
                },
            )
        self.client = APIClient()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "emp@test.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_rejects_unsupported_audio_extension(self):
        bad_file = SimpleUploadedFile("recording.exe", b"fake", content_type="application/octet-stream")
        response = self.client.post(
            "/api/v1/integrations/recordings/",
            {
                "client_name": "Test Client",
                "employee_id": str(self.employee.id),
                "audio_file": bad_file,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("audio_file", response.data)

    @patch("integrations.serializers.AUDIO_MAX_SIZE_MB", 1)
    def test_rejects_oversize_audio_file(self):
        big_file = SimpleUploadedFile("recording.mp3", b"x" * (2 * 1024 * 1024), content_type="audio/mpeg")
        response = self.client.post(
            "/api/v1/integrations/recordings/",
            {
                "client_name": "Test Client",
                "employee_id": str(self.employee.id),
                "audio_file": big_file,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("audio_file", response.data)
        self.assertIn("too large", str(response.data["audio_file"]).lower())
