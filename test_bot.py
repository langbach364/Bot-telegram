import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from bot import app


class WebhookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test-token", "WEBHOOK_SECRET": "test-secret"},
        )
        self.environment.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.environment.stop()

    def test_rejects_request_without_telegram_secret(self) -> None:
        response = self.client.post("/webhook", json={})
        self.assertEqual(response.status_code, 403)

    @patch("bot._set_webhook", new_callable=AsyncMock)
    def test_setup_registers_webhook_url(self, set_webhook: AsyncMock) -> None:
        response = self.client.get("/setup?secret=test-secret")

        self.assertEqual(response.status_code, 200)
        set_webhook.assert_awaited_once_with(
            "http://testserver/webhook", "test-secret"
        )

    def test_returns_normalized_coordinates_to_telegram(self) -> None:
        response = self.client.post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
            json={
                "message": {
                    "text": "10,90242° B, 106,59664° Đ",
                    "chat": {"id": 12345},
                }
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "method": "sendMessage",
                "chat_id": 12345,
                "text": "10.90242, 106.59664",
            },
        )

    def test_start_returns_usage(self) -> None:
        response = self.client.post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
            json={"message": {"text": "/start", "chat": {"id": 12345}}},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("10,90242° B", response.json()["text"])


if __name__ == "__main__":
    unittest.main()
