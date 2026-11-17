import json

from app.database.database import db
from app.models.push_subscription import PushSubscription
from flask import current_app
from pywebpush import WebPushException, webpush


def disparar_notificacao_pedido(user_id, titulo, mensagem, url="/minha-conta/historico-compras"):
    inscricoes = PushSubscription.query.filter_by(user_id=user_id).all()
    if not inscricoes:
        return

    private_key = current_app.config.get("VAPID_PRIVATE_KEY")
    claim_email = current_app.config.get("VAPID_CLAIM_EMAIL", "mailto:suporte@candyland.com")

    payload = json.dumps({
        "title": titulo,
        "body": mensagem,
        "url": url
    })

    for sub in inscricoes:
        try:
            webpush(
                subscription_info=sub.to_pay_info(),
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": claim_email}
            )
        except WebPushException as ex:
            # Se a inscrição expirou no navegador do cliente, limpa do banco
            if ex.response and ex.response.status_code in (404, 410):
                db.session.delete(sub)
                db.session.commit()