from flask import jsonify, make_response

from app.services.recommendation_service import RecommendationService


class RecommendationController:
    @staticmethod
    def _ler_ids(args):
        """Aceita ?produto_id=1&produto_id=2 e também ?produtos=1,2,3."""
        brutos = list(args.getlist("produto_id"))
        for grupo in args.getlist("produtos"):
            brutos.extend(parte for parte in grupo.split(","))
        return [b.strip() for b in brutos if b.strip() != ""]

    @staticmethod
    def recomendar(args):
        ids = RecommendationController._ler_ids(args)
        if not ids:
            return make_response(jsonify({"erro": "Informe ao menos um produto (produto_id)."}), 400)

        resultado = RecommendationService.recomendar(ids, args.get("limite", 6))
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        dados = resultado["dados"]
        return make_response(jsonify({
            "mensagem": resultado["mensagem"],
            "restaurante_id": dados["restaurante_id"],
            "base": dados["base"],
            "recomendacoes": dados["recomendacoes"],
        }), 200)