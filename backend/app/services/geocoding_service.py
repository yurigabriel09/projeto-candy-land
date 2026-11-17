"""Geocodificação server-side compartilhada pelos fluxos de endereço.

O cliente informa endereço e número. Latitude/longitude são resolvidas no backend
com uma chave restrita à API Geocoding, nunca recebida do aplicativo.
"""
import math

import requests
from flask import current_app


class GeocodingService:
    @staticmethod
    def geocodificar(endereco_dados):
        """Resolve texto de endereço livre ou os campos de um endereço salvo."""
        if isinstance(endereco_dados, str):
            endereco = endereco_dados.strip()
            if len(endereco) < 8:
                return {"success": False, "erro": "Informe um endereço completo, incluindo número e cidade.", "status_code": 400}
            if len(endereco) > 250:
                return {"success": False, "erro": "O endereço deve possuir no máximo 250 caracteres.", "status_code": 400}
            consulta = f"{endereco}, Brasil"
        elif isinstance(endereco_dados, dict):
            campos = {
                "rua": str(endereco_dados.get("rua") or "").strip(),
                "numero": str(endereco_dados.get("numero") or "").strip(),
                "bairro": str(endereco_dados.get("bairro") or "").strip(),
                "cidade": str(endereco_dados.get("cidade") or "").strip(),
                "estado": str(endereco_dados.get("estado") or "").strip().upper(),
                "cep": str(endereco_dados.get("cep") or "").strip(),
            }
            obrigatorios = ("rua", "numero", "cidade", "estado")
            ausentes = [campo for campo in obrigatorios if not campos[campo]]
            if ausentes:
                return {
                    "success": False,
                    "erro": "Preencha rua, número, cidade e estado para localizar o endereço.",
                    "status_code": 400,
                }
            consulta = ", ".join(
                parte for parte in (
                    campos["rua"], campos["numero"], campos["bairro"],
                    campos["cidade"], campos["estado"], campos["cep"], "Brasil",
                ) if parte
            )
        else:
            return {"success": False, "erro": "Informe um endereço válido.", "status_code": 400}

        api_key = str(current_app.config.get("GOOGLE_MAPS_GEOCODING_API_KEY", "") or "").strip()
        if not api_key:
            return {
                "success": False,
                "erro": (
                    "A geolocalização automática não está configurada. Configure "
                    "GOOGLE_MAPS_GEOCODING_API_KEY no backend/.env e habilite a API "
                    "Geocoding no Google Cloud."
                ),
                "status_code": 503,
            }

        try:
            resposta = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": consulta,
                    "key": api_key,
                    "region": "br",
                    "components": "country:BR",
                },
                timeout=8,
            )
            resposta.raise_for_status()
            payload = resposta.json()
        except (requests.RequestException, ValueError):
            return {
                "success": False,
                "erro": "Não foi possível consultar o mapa agora. Confira a conexão e tente novamente.",
                "status_code": 502,
            }

        status = str(payload.get("status", "")) if isinstance(payload, dict) else ""
        resultados = payload.get("results") or [] if isinstance(payload, dict) else []
        if status != "OK" or not resultados:
            mensagens = {
                "ZERO_RESULTS": (
                    "Não encontramos esse endereço no mapa. Confira CEP, rua, número, bairro e cidade."
                ),
                "REQUEST_DENIED": (
                    "O Google recusou a geocodificação. Confira a chave e se a API Geocoding está habilitada."
                ),
                "OVER_QUERY_LIMIT": (
                    "O limite de consultas do mapa foi atingido. Tente novamente mais tarde."
                ),
            }
            mensagem = mensagens.get(
                status, "Não foi possível localizar esse endereço. Confira os dados e tente novamente."
            )
            codigo_http = 422 if status == "ZERO_RESULTS" else 503 if status in {"REQUEST_DENIED", "OVER_QUERY_LIMIT"} else 502
            return {"success": False, "erro": mensagem, "status_code": codigo_http}

        try:
            local = resultados[0]["geometry"]["location"]
            latitude = float(local["lat"])
            longitude = float(local["lng"])
        except (KeyError, TypeError, ValueError):
            return {
                "success": False,
                "erro": "O serviço de mapas retornou uma localização inválida. Confira o endereço.",
                "status_code": 502,
            }

        if not (
            math.isfinite(latitude) and math.isfinite(longitude)
            and -90 <= latitude <= 90 and -180 <= longitude <= 180
        ):
            return {
                "success": False,
                "erro": "O serviço de mapas retornou uma localização fora dos limites válidos.",
                "status_code": 502,
            }

        return {
            "success": True,
            "mensagem": "Endereço localizado no mapa.",
            "dados": {
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "endereco_localizado": resultados[0].get("formatted_address"),
            },
        }
