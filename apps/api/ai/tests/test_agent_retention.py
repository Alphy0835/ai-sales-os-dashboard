from django.test import TestCase
from django.utils import timezone

from accounts.models import Tenant, User, Workspace
from ai.models import AgentChatMessage, AgentChatSession
from ai.tasks import purge_expired_agent_chats


class AgentRetentionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Chat Co", slug="chat-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.user = User.objects.create_user(
            email="mgr@chat.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )

    def test_purge_deletes_old_sessions(self):
        old = AgentChatSession.objects.create(
            tenant=self.tenant,
            user=self.user,
            agent_role=AgentChatSession.AgentRole.MANAGER,
            client_name="Old",
        )
        AgentChatMessage.objects.create(
            session=old,
            role=AgentChatMessage.Role.USER,
            content="hello",
        )
        AgentChatSession.objects.filter(id=old.id).update(
            updated_at=timezone.now() - timezone.timedelta(days=91)
        )
        recent = AgentChatSession.objects.create(
            tenant=self.tenant,
            user=self.user,
            agent_role=AgentChatSession.AgentRole.MANAGER,
            client_name="Recent",
        )
        result = purge_expired_agent_chats()
        self.assertEqual(result["deleted"], 1)
        self.assertFalse(AgentChatSession.objects.filter(id=old.id).exists())
        self.assertTrue(AgentChatSession.objects.filter(id=recent.id).exists())
