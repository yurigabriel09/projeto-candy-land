from datetime import date
from decimal import Decimal

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models.address import Endereco
from app.models.auth_attempt import TentativaAutenticacao
from app.models.push_subscription import PushSubscription
from app.models.user import Usuario
from app.services.account_identity_service import (
    email_esta_em_uso,
    telefone_esta_em_uso,
)
from app.services.geocoding_service import GeocodingService
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

            if not isinstance(endereco, dict):
                return {"success": False, "erro": "Informe um endereço residencial completo.", "status_code": 400}
            geocodificacao = GeocodingService.geocodificar(endereco)
            if not geocodificacao["success"]:
                # Evita cadastrar endereço sem localização, pois o cálculo de frete
                # e a entrega dependem das coordenadas desse endereço.
                return geocodificacao
            coordenadas = geocodificacao["dados"]

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
                latitude=coordenadas["latitude"],
                longitude=coordenadas["longitude"],
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
        """Resolve e persiste a localização do endereço do próprio cliente."""
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

        resultado = GeocodingService.geocodificar({
            "cep": endereco.cep, "rua": endereco.rua, "numero": endereco.numero,
            "bairro": endereco.bairro, "cidade": endereco.cidade, "estado": endereco.estado,
        })
        if not resultado["success"]:
            return resultado
        try:
            endereco.latitude = Decimal(str(resultado["dados"]["latitude"])).quantize(Decimal("0.000001"))
            endereco.longitude = Decimal(str(resultado["dados"]["longitude"])).quantize(Decimal("0.000001"))
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Endereço localizado e coordenadas salvas.",
                "dados": endereco.to_dict(),
                "endereco_localizado": resultado["dados"].get("endereco_localizado"),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Não foi possível salvar a localização do endereço.",
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
        except ValueError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Data de nascimento inválida. Use o formato AAAA-MM-DD.",
                "status_code": 400,
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

    @staticmethod
    def listar_enderecos_usuario(user_id):
        try:
            enderecos = Endereco.query.filter_by(id_usuario=user_id, ativo=True).all()
            return {
                "success": True,
                "mensagem": "Endereços consultados com sucesso.",
                "dados": [e.to_dict() for e in enderecos],
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar endereços do usuário.",
                "status_code": 500,
            }


    @staticmethod
    def cadastrar_endereco_usuario(user_id, dados_endereco):
        if not isinstance(dados_endereco, dict):
            return {
                "success": False,
                "erro": "Dados do endereço inválidos.",
                "status_code": 400,
            }
        try:
            usuario = db.session.get(Usuario, user_id)
            if not usuario:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}

            address_id = dados_endereco.get("id")
            endereco_existente = None
            if address_id:
                endereco_existente = Endereco.query.filter_by(
                    id=address_id, id_usuario=user_id, ativo=True
                ).first()
                if endereco_existente is None:
                    return {
                        "success": False,
                        "erro": "Endereço não encontrado para este cliente.",
                        "status_code": 404,
                    }

            campos_localizacao = ("cep", "rua", "numero", "bairro", "cidade", "estado")
            endereco_alterado = endereco_existente is None or any(
                campo in dados_endereco
                and str(getattr(endereco_existente, campo, "") or "").strip()
                != str(dados_endereco.get(campo) or "").strip()
                for campo in campos_localizacao
            )
            if endereco_alterado or endereco_existente.latitude is None or endereco_existente.longitude is None:
                dados_geo = {
                    campo: dados_endereco.get(
                        campo,
                        getattr(endereco_existente, campo, None) if endereco_existente else None
                    )
                    for campo in campos_localizacao
                }
                geocodificacao = GeocodingService.geocodificar(dados_geo)
                if geocodificacao["success"]:
                    latitude = geocodificacao["dados"]["latitude"]
                    longitude = geocodificacao["dados"]["longitude"]
                elif geocodificacao.get("status_code") in (502, 503):
                    latitude = longitude = None
                else:
                    return geocodificacao
            else:
                latitude = float(endereco_existente.latitude)
                longitude = float(endereco_existente.longitude)

            if dados_endereco.get("principal"):
                Endereco.query.filter_by(id_usuario=user_id).update({"principal": False})

            if endereco_existente:
                endereco_existente.cep = dados_endereco.get("cep")
                endereco_existente.rua = dados_endereco.get("rua")
                endereco_existente.numero = dados_endereco.get("numero")
                endereco_existente.complemento = dados_endereco.get("complemento")
                endereco_existente.bairro = dados_endereco.get("bairro")
                endereco_existente.cidade = dados_endereco.get("cidade")
                endereco_existente.estado = dados_endereco.get("estado")
                endereco_existente.referencia = dados_endereco.get("referencia")
                endereco_existente.latitude = latitude
                endereco_existente.longitude = longitude
                if "principal" in dados_endereco:
                    endereco_existente.principal = dados_endereco.get("principal")
                target_endereco = endereco_existente
            else:
                novo_endereco = Endereco(
                    id_usuario=user_id,
                    cep=dados_endereco.get("cep"),
                    rua=dados_endereco.get("rua"),
                    numero=dados_endereco.get("numero"),
                    complemento=dados_endereco.get("complemento"),
                    bairro=dados_endereco.get("bairro"),
                    cidade=dados_endereco.get("cidade"),
                    estado=dados_endereco.get("estado"),
                    referencia=dados_endereco.get("referencia"),
                    latitude=latitude,
                    longitude=longitude,
                    tipo_endereco="RESIDENCIAL",
                    principal=dados_endereco.get("principal", False),
                    ativo=True
                )
                db.session.add(novo_endereco)
                target_endereco = novo_endereco

            db.session.commit()

            return {
                "success": True,
                "mensagem": "Endereço salvo com sucesso!",
                "dados": target_endereco.to_dict()
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao salvar endereço.", "status_code": 500}

    @staticmethod
    def deletar_endereco_usuario(user_id, address_id):
        try:
            endereco = Endereco.query.filter_by(
                id=address_id, id_usuario=user_id, ativo=True
            ).first()
            if not endereco:
                return {
                    "success": False,
                    "erro": "Endereço não encontrado ou já removido.",
                    "status_code": 404,
                }

            endereco.ativo = False
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Endereço removido com sucesso!",
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao remover o endereço.",
                "status_code": 500,
            }


    @staticmethod
    def salvar_push_subscription(user_id, dados):
        if not isinstance(dados, dict):
            return {
                "success": False,
                "erro": "Dados de inscrição Web Push inválidos.",
                "status_code": 400,
            }
        try:
            endpoint = dados.get("endpoint")
            keys = dados.get("keys") or {}
            if not isinstance(keys, dict):
                return {
                    "success": False,
                    "erro": "Chaves da inscrição Web Push inválidas.",
                    "status_code": 400,
                }
            p256dh = keys.get("p256dh")
            auth = keys.get("auth")

            if not endpoint or not p256dh or not auth:
                return {
                    "success": False,
                    "erro": "Dados de inscrição Web Push incompletos.",
                    "status_code": 400,
                }

            # Verifica se essa inscrição de navegador já foi registrada para o usuário
            sub_existente = PushSubscription.query.filter_by(endpoint=endpoint).first()
            if not sub_existente:
                nova_sub = PushSubscription(
                    user_id=user_id,
                    endpoint=endpoint,
                    p256dh=p256dh,
                    auth=auth,
                )
                db.session.add(nova_sub)
                db.session.commit()

            return {
                "success": True,
                "mensagem": "Inscrição de notificação salva com sucesso.",
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao salvar a inscrição de notificação.",
                "status_code": 500,
            }