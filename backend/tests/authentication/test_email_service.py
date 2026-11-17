import pytest
import requests
from app.services.email_service import EmailService


def _configure_brevo(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "brevo-test-key")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "no-reply@example.com")
    monkeypatch.setenv("BREVO_SENDER_NAME", "CandyLand Test")


def test_email_service_sends_otp_through_brevo(monkeypatch):
    _configure_brevo(monkeypatch)
    calls = {}

    class Response:
        ok = True
        status_code = 201

    def fake_post(url, **kwargs):
        calls["url"] = url
        calls.update(kwargs)
        return Response()

    monkeypatch.setattr("app.services.email_service.requests.post", fake_post)
    EmailService.enviar_codigo("cliente@example.com", "123456")

    assert calls["url"] == "https://api.brevo.com/v3/smtp/email"
    assert calls["headers"]["api-key"] == "brevo-test-key"
    assert calls["json"]["to"] == [{"email": "cliente@example.com"}]
    assert "123456" in calls["json"]["textContent"]
    assert calls["timeout"] == (3.05, 10)


def test_email_service_fails_clearly_without_brevo_configuration(monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    monkeypatch.delenv("BREVO_SENDER_EMAIL", raising=False)

    with pytest.raises(ValueError, match="Brevo"):
        EmailService.enviar_codigo("cliente@example.com", "123456")


def test_email_service_converts_network_errors_to_actionable_failure(monkeypatch):
    _configure_brevo(monkeypatch)

    def fail_request(*args, **kwargs):
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr("app.services.email_service.requests.post", fail_request)

    with pytest.raises(ValueError, match="indisponível"):
        EmailService.enviar_codigo("cliente@example.com", "123456")


def test_email_service_reports_brevo_rejection_without_logging_payload(monkeypatch, caplog):
    _configure_brevo(monkeypatch)

    class Response:
        ok = False
        status_code = 401
        text = "sensitive provider response"

    monkeypatch.setattr(
        "app.services.email_service.requests.post",
        lambda *args, **kwargs: Response(),
    )

    with pytest.raises(ValueError, match="chave de API"):
        EmailService.enviar_codigo("cliente@example.com", "123456")

    assert "sensitive provider response" not in caplog.text
    assert "123456" not in caplog.text
    assert "cliente@example.com" not in caplog.text
