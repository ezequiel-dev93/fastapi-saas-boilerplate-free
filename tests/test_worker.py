from unittest.mock import patch

import pytest

from api.worker import enqueue_job, task_send_email, task_send_invitation_email


@pytest.mark.asyncio
async def test_task_send_email_direct_execution():
    """Test that task_send_email worker function delegates to send_email."""
    with patch("api.worker.send_email") as mock_send:
        await task_send_email(
            ctx={},
            to_email="worker_test@example.com",
            subject="Job Subject",
            body_text="Job Body",
        )
        mock_send.assert_called_once_with(
            to_email="worker_test@example.com",
            subject="Job Subject",
            body_text="Job Body",
            body_html=None,
        )


@pytest.mark.asyncio
async def test_task_send_invitation_email_direct_execution():
    """Test that task_send_invitation_email delegates to send_organization_invitation_email."""
    with patch("api.worker.send_organization_invitation_email") as mock_send_invite:
        await task_send_invitation_email(
            ctx={},
            to_email="colleague@example.com",
            org_name="Innovate Corp",
            inviter_name="Alice",
            token="secure-token-123",
            role="admin",
        )
        mock_send_invite.assert_called_once_with(
            to_email="colleague@example.com",
            org_name="Innovate Corp",
            inviter_name="Alice",
            token="secure-token-123",
            role="admin",
        )


@pytest.mark.asyncio
async def test_enqueue_job_fallback_without_redis():
    """When Redis is not reachable, enqueue_job gracefully falls back to direct execution."""
    with patch("api.worker.send_email") as mock_send:
        # Without Redis running, should return False (fallback executed) without raising an exception
        result = await enqueue_job(
            "task_send_email",
            to_email="fallback@example.com",
            subject="Fallback Subject",
            body_text="Fallback Body",
        )
        assert result is False
        mock_send.assert_called_once()
