from django.contrib import admin
from django.test import TestCase
from unittest.mock import MagicMock

from accounts.admin import RegistrationInviteInline, WorkspaceAdmin
from accounts.models import Workspace
from ai.admin import WorkspaceAiConfigInline
from ai.models import WorkspaceAiConfig


class IntegratorAdminTests(TestCase):
    def test_workspace_admin_registers_integrator_inlines(self):
        workspace_admin = admin.site._registry[Workspace]

        self.assertIsInstance(workspace_admin, WorkspaceAdmin)
        self.assertIn(WorkspaceAiConfigInline, workspace_admin.inlines)
        self.assertIn(RegistrationInviteInline, workspace_admin.inlines)
        self.assertEqual(
            [inline.model for inline in workspace_admin.inlines],
            [WorkspaceAiConfigInline.model, RegistrationInviteInline.model],
        )

    def test_workspace_admin_has_integrator_fieldsets(self):
        workspace_admin = admin.site._registry[Workspace]
        fieldset_titles = [title for title, _ in workspace_admin.fieldsets]

        self.assertIn("Integrator", fieldset_titles)
        self.assertIn("Основное", fieldset_titles)
        self.assertIn("crm_sources_link", workspace_admin.readonly_fields)

    def test_registration_invite_inline_readonly_fields(self):
        self.assertIn("use_count", RegistrationInviteInline.readonly_fields)
        self.assertIn("registration_url_display", RegistrationInviteInline.readonly_fields)

    def test_workspace_admin_save_formset_handles_ai_config_inline(self):
        from accounts.models import Tenant

        tenant = Tenant.objects.create(name="Inline Co", slug="inline-co")
        workspace = Workspace.objects.create(tenant=tenant, name="Office")
        ai_config = WorkspaceAiConfig(workspace=workspace, model_tier="free")
        form = MagicMock()
        form.instance = workspace
        formset = MagicMock()
        formset.save.return_value = [ai_config]
        formset.deleted_objects = []

        admin_instance = admin.site._registry[Workspace]
        admin_instance.save_formset(None, form, formset, change=True)

        ai_config.refresh_from_db()
        self.assertEqual(ai_config.model_tier, "free")
