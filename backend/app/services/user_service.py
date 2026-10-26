import math
from datetime import date
from decimal import Decimal, InvalidOperation

import requests

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models.address import Endereco
from app.models.auth_attempt import TentativaAutenticacao
from app.models.restaurant import Restaurante
from app.models.user import Usuario
from app.services.account_identity_service import (
    email_esta_em_uso,
    telefone_esta_em_uso,
)
from app.services.token_service import TokenService
from app.utils.formatter import normalizar_telefone
from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class UserService:
    @staticmethod
    def listar_usuarios():
        try:
            usuarios = Usuario.query.all()
            if not usuarios:
                return {
                    "success": True,
                    "mensagem": "Nenhum usuário cadastrado!",
                    "dados": [],
                }
            return {
                "success": True,
                "mensagem": "Lista de usuários cadastrados:",
                "dados": [usuario.to_dict() for usuario in usuarios],
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar o banco de dados.",
                "status_code": 500,
            }

    @staticmethod
    def buscar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            return {
                "success": True,
                "mensagem": "Usuário encontrado:",
                "dados": usuario.to_dict(),
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar o banco de dados.",
                "status_code": 500,
            }

    @staticmethod
    def listar_enderecos(user_id):
        """Lista apenas os endereços ativos pertencentes ao cliente autenticado."""
        try:
            enderecos = (
                Endereco.query.filter_by(id_usuario=user_id, ativo=True)
                .order_by(Endereco.principal.desc(), Endereco.id.asc())
                .all()
            )
            return {
                "success": True,
                "mensagem": "Endereços ativos consultados.",
                "dados": [endereco.to_dict() for endereco in enderecos],
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar os endereços do cliente.",
                "status_code": 500,
            }

    @staticmethod
    def criar_usuario(
        nome_completo,
        email,
        telefone,
        cpf,
        tentativa_id,
        data_nascimento=None,
        endereco=None,
    ):
        try:
            if not tentativa_id:
                return {
                    "success": False,
                    "erro": "Verificação de segurança (tentativa_id) é obrigatória.",
                    "status_code": 400,
                }

            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)

            if not tentativa:
                return {
                    "success": False,
                    "erro": "Verificação de segurança não encontrada.",
                    "status_code": 404,
                }

            if (
                not tentativa.concluida
                or not tentativa.email_validado
                or not tentativa.telefone_validado
            ):
                return {
                    "success": False,
                    "erro": "Verificação por e-mail e WhatsApp ainda não foi concluída.",
                    "status_code": 401,
                }

            # Usa os dados verificados na tentativa como fonte de verdade.
            email = (tentativa.email or email or "").strip().lower()
            telefone = tentativa.telefone or telefone

            if not email:
                return {
                    "success": False,
                    "erro": "E-mail verificado é obrigatório para criar a conta.",
                    "status_code": 400,
                }

            # O e-mail deve identificar no máximo uma conta em toda a plataforma,
            # não apenas dentro da tabela de clientes.
            if email_esta_em_uso(email):
                return {
                    "success": False,
                    "erro": "E-mail já cadastrado em outra conta.",
                    "status_code": 409,
                }

            telefone_normalizado = normalizar_telefone(telefone)
            if (
                not telefone_compartilhado_permitido(current_app.config)
                and telefone_esta_em_uso(telefone_normalizado)
            ):
                return {
                    "success": False,
                    "erro": "Telefone já cadastrado.",
                    "status_code": 409,
                }

            if data_nascimento:
                data_nascimento = date.fromisoformat(data_nascimento)

            novo_usuario = Usuario(
                nome_completo=nome_completo,
                email=email,
                telefone=normalizar_telefone(telefone),
                cpf=cpf,
                data_nascimento=data_nascimento,
            )

            db.session.add(novo_usuario)
            db.session.flush()

            novo_endereco = Endereco(
                id_usuario=novo_usuario.id,
                cep=endereco.get("cep"),
                rua=endereco.get("rua"),
                numero=endereco.get("numero"),
                complemento=endereco.get("complemento"),
                bairro=endereco.get("bairro"),
                cidade=endereco.get("cidade"),
                estado=endereco.get("estado"),
                referencia=endereco.get("referencia"),
                latitude=endereco.get("latitude"),
                longitude=endereco.get("longitude"),
                tipo_endereco="RESIDENCIAL",
                principal=True,
                ativo=True,
            )

            db.session.add(novo_endereco)
            db.session.commit()

            return {
                "success": True,
                "mensagem": "Usuário e endereço criados com sucesso!",
                "dados": {
                    "usuario": novo_usuario.to_dict(),
                    "endereco": novo_endereco.to_dict(),
                    "token": TokenService.gerar_token(
                        "PERSONAL", novo_usuario.id, novo_usuario.email
                    ),
                },
            }

        except ValueError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Data de nascimento inválida.",
                "status_code": 400,
            }

        except IntegrityError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "E-mail, telefone ou CPF já cadastrado.",
                "status_code": 409,
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao criar usuário e endereço.",
                "status_code": 500,
            }

    @staticmethod
    def geocodificar_endereco(user_id, address_id):
        """Resolve the selected customer's saved address and persists its coordinates.

        The request is made only when the user selects an address without coordinates.
        It uses the server-side Google Geocoding API key; no address or key is exposed
        to the React client.
        """
        endereco = Endereco.query.filter_by(
            id=address_id, id_usuario=user_id, ativo=True
        ).first()
        if not endereco:
            return {
                "success": False,
                "erro": "Endereço ativo não encontrado para este cliente.",
                "status_code": 404,
            }

        if endereco.latitude is not None and endereco.longitude is not None:
            return {
                "success": True,
                "mensagem": "Este endereço já possui coordenadas salvas.",
                "dados": endereco.to_dict(),
            }

        api_key = str(current_app.config.get("GOOGLE_MAPS_GEOCODING_API_KEY", "") or "").strip()
        if not api_key:
            return {
                "success": False,
                "erro": (
                    "A localização automática ainda não está configurada. Configure "
                    "GOOGLE_MAPS_GEOCODING_API_KEY no backend/.env e habilite a API "
                    "Geocoding no Google Cloud, ou informe a localização manualmente."
                ),
                "status_code": 503,
            }

        linhas = [endereco.rua, endereco.numero, endereco.bairro, endereco.cidade, endereco.estado, endereco.cep, "Brasil"]
        consulta = ", ".join(str(item).strip() for item in linhas if item and str(item).strip())
        try:
            resposta = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": consulta, "key": api_key, "region": "br", "components": "country:BR"},
                timeout=8,
            )
            resposta.raise_for_status()
            payload = resposta.json()
        except (requests.RequestException, ValueError):
            return {
                "success": False,
                "erro": "Não foi possível consultar a localização agora. Tente novamente ou informe as coordenadas manualmente.",
                "status_code": 502,
            }

        if not isinstance(payload, dict):
            return {
                "success": False,
                "erro": "O serviço de localização retornou uma resposta inválida.",
                "status_code": 502,
            }
        status = str(payload.get("status", ""))
        resultados = payload.get("results") or []
        if status != "OK" or not resultados:
            mensagem = {
                "ZERO_RESULTS": "Não encontramos esse endereço no mapa. Confira rua, número, bairro, cidade e CEP.",
                "REQUEST_DENIED": "O Google recusou a geocodificação. Confira a chave e se a API Geocoding está habilitada no Google Cloud.",
                "OVER_QUERY_LIMIT": "O limite de consultas de localização foi atingido. Tente novamente mais tarde.",
            }.get(status, "Não foi possível localizar esse endereço automaticamente. Confira os dados ou informe as coordenadas manualmente.")
            return {"success": False, "erro": mensagem, "status_code": 422}

        try:
            local = resultados[0]["geometry"]["location"]
            latitude = float(local["lat"])
            longitude = float(local["lng"])
        except (KeyError, TypeError, ValueError):
            return {
                "success": False,
                "erro": "O serviço de localização retornou coordenadas inválidas.",
                "status_code": 502,
            }

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return {
                "success": False,
                "erro": "O serviço retornou uma localização fora dos limites válidos.",
                "status_code": 502,
            }

        try:
            endereco.latitude = Decimal(str(latitude)).quantize(Decimal("0.000001"))
            endereco.longitude = Decimal(str(longitude)).quantize(Decimal("0.000001"))
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Endereço localizado e coordenadas salvas.",
                "dados": endereco.to_dict(),
                "endereco_localizado": payload["results"][0].get("formatted_address"),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Não foi possível salvar as coordenadas do endereço.",
                "status_code": 500,
            }

    @staticmethod
    def atualizar_coordenadas_endereco(user_id, address_id, latitude, longitude):
        """Salva coordenadas somente em endereço ativo do cliente autenticado."""
        try:
            try:
                lat = float(latitude)
                lon = float(longitude)
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "erro": "Informe latitude e longitude numéricas.",
                    "status_code": 400,
                }
            if (
                not math.isfinite(lat)
                or not math.isfinite(lon)
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
            ):
                return {
                    "success": False,
                    "erro": "Latitude deve estar entre -90 e 90 e longitude entre -180 e 180.",
                    "status_code": 400,
                }

            endereco = Endereco.query.filter_by(
                id=address_id, id_usuario=user_id, ativo=True
            ).first()
            if not endereco:
                return {
                    "success": False,
                    "erro": "Endereço ativo não encontrado para este cliente.",
                    "status_code": 404,
                }
            endereco.latitude = Decimal(str(lat)).quantize(Decimal("0.000001"))
            endereco.longitude = Decimal(str(lon)).quantize(Decimal("0.000001"))
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Coordenadas do endereço salvas.",
                "dados": endereco.to_dict(),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao salvar as coordenadas do endereço.",
                "status_code": 500,
            }

    @staticmethod
    def atualizar_usuario(
        user_id, nome_completo=None, email=None, telefone=None, data_nascimento=None
    ):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            if nome_completo is not None:
                usuario.nome_completo = nome_completo
            if email is not None:
                email_normalizado = email.strip().lower()
                if email_esta_em_uso(
                    email_normalizado, usuario_id_ignorar=usuario.id
                ):
                    return {
                        "success": False,
                        "erro": "E-mail já cadastrado em outra conta.",
                        "status_code": 409,
                    }
                usuario.email = email_normalizado
            if telefone is not None:
                telefone_normalizado = normalizar_telefone(telefone)
                if (
                    not telefone_compartilhado_permitido(current_app.config)
                    and telefone_esta_em_uso(
                        telefone_normalizado, usuario_id_ignorar=usuario.id
                    )
                ):
                    return {
                        "success": False,
                        "erro": "Telefone já cadastrado em outra conta.",
                        "status_code": 409,
                    }
                usuario.telefone = telefone_normalizado
            if data_nascimento is not None:
                data_nascimento = date.fromisoformat(data_nascimento)
                usuario.data_nascimento = data_nascimento
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Usuário atualizado com sucesso!",
                "dados": usuario.to_dict(),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao atualizar usuário.",
                "status_code": 500,
            }

    @staticmethod
    def deletar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            db.session.delete(usuario)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao remover usuário.",
                "status_code": 500,
            }
