from decimal import Decimal, InvalidOperation

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


class RestauranteService:
    @staticmethod
    def _validar_valor_nao_negativo(valor, campo):
        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{campo} deve ser um valor numérico válido.")
        if not numero.is_finite() or numero < 0:
            raise ValueError(f"{campo} não pode ser negativo nem inválido.")
        return numero.quantize(Decimal("0.01"))

    @staticmethod
    def _validar_raio(valor):
        if valor in (None, ""):
            return None
        try:
            raio = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("raio_entrega_km deve ser numérico.")
        if not raio.is_finite() or raio <= 0:
            raise ValueError("raio_entrega_km deve ser maior que zero.")
        return raio.quantize(Decimal("0.01"))

    @staticmethod
    def listar_restaurantes():
        try:
            restaurantes = Restaurante.query.all()
            if not restaurantes:
                return {"success": True, "mensagem": "Nenhum restaurante cadastrado!", "dados": []}
            return {
                "success": True,
                "mensagem": "Lista de restaurantes cadastrados:",
                "dados": [restaurante.to_catalog_dict() for restaurante in restaurantes],
            }
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def buscar_restaurante(restaurante_id):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            return {"success": True, "mensagem": "Restaurante encontrado:", "dados": restaurante.to_catalog_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def listar_enderecos_retirada(restaurante_id):
        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante or not restaurante.ativo:
                return {"success": False, "erro": "Restaurante não encontrado ou indisponível.", "status_code": 404}
            from sqlalchemy import or_
            filtro = Endereco.id_restaurante == restaurante_id
            if restaurante.address_id:
                filtro = or_(filtro, Endereco.id == restaurante.address_id)
            enderecos = (
                Endereco.query.filter(filtro, Endereco.ativo.is_(True))
                .order_by(Endereco.principal.desc(), Endereco.id.asc())
                .all()
            )
            resultado = []
            ids_vistos = set()
            for endereco in enderecos:
                if endereco.id in ids_vistos:
                    continue
                ids_vistos.add(endereco.id)
                resultado.append({
                    "id": endereco.id,
                    "cep": endereco.cep,
                    "rua": endereco.rua,
                    "numero": endereco.numero,
                    "complemento": endereco.complemento,
                    "bairro": endereco.bairro,
                    "cidade": endereco.cidade,
                    "estado": endereco.estado,
                    "referencia": endereco.referencia,
                    "latitude": float(endereco.latitude) if endereco.latitude is not None else None,
                    "longitude": float(endereco.longitude) if endereco.longitude is not None else None,
                    "principal": bool(endereco.principal),
                    "ativo": bool(endereco.ativo),
                })
            return {"success": True, "mensagem": "Endereços de retirada consultados.", "dados": resultado}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar os endereços do restaurante.", "status_code": 500}

    @staticmethod
    def criar_restaurante(
        cnpj, razao_social, nome, email, telefone, cpf_responsavel,
        tentativa_id, endereco, nome_responsavel=None, descricao=None,
        valor_minimo_pedido=None, taxa_entrega_base=None, taxa_entrega_por_km=0,
        raio_entrega_km=None, horario_funcionamento=None,
    ):
        try:
            if not tentativa_id:
                return {"success": False, "erro": "Verificação de segurança (tentativa_id) é obrigatória.", "status_code": 400}
            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)
            if not tentativa:
                return {"success": False, "erro": "Verificação de segurança não encontrada.", "status_code": 404}
            if not tentativa.concluida or not tentativa.email_validado or not tentativa.telefone_validado:
                return {"success": False, "erro": "Verificação por e-mail e WhatsApp ainda não foi concluída.", "status_code": 401}

            email = (tentativa.email or email or "").strip().lower()
            telefone = tentativa.telefone or telefone
            if not email:
                return {"success": False, "erro": "E-mail verificado é obrigatório para criar a conta.", "status_code": 400}
            if email_esta_em_uso(email):
                return {"success": False, "erro": "E-mail já cadastrado em outra conta.", "status_code": 409}
            telefone_normalizado = normalizar_telefone(telefone)
            if not telefone_normalizado:
                return {"success": False, "erro": "Telefone inválido.", "status_code": 400}
            if not telefone_compartilhado_permitido(current_app.config) and telefone_esta_em_uso(telefone_normalizado):
                return {"success": False, "erro": "Telefone já cadastrado.", "status_code": 409}

            novo_restaurante = Restaurante(
                cnpj=cnpj, razao_social=razao_social, nome=nome,
                nome_responsavel=nome_responsavel, email=email,
                telefone=telefone_normalizado, cpf_responsavel=cpf_responsavel,
                descricao=descricao, valor_minimo_pedido=valor_minimo_pedido or 0,
                taxa_entrega_base=RestauranteService._validar_valor_nao_negativo(
                    taxa_entrega_base if taxa_entrega_base is not None else 0, "taxa_entrega_base",
                ),
                taxa_entrega_por_km=RestauranteService._validar_valor_nao_negativo(
                    taxa_entrega_por_km if taxa_entrega_por_km is not None else 0, "taxa_entrega_por_km",
                ),
                raio_entrega_km=RestauranteService._validar_raio(raio_entrega_km),
                horario_funcionamento=horario_funcionamento,
            )
            db.session.add(novo_restaurante)
            db.session.flush()
            novo_endereco = Endereco(
                id_restaurante=novo_restaurante.id,
                cep=endereco.get("cep"), rua=endereco.get("rua"), numero=endereco.get("numero"),
                complemento=endereco.get("complemento"), bairro=endereco.get("bairro"),
                cidade=endereco.get("cidade"), estado=endereco.get("estado"),
                referencia=endereco.get("referencia"), latitude=endereco.get("latitude"),
                longitude=endereco.get("longitude"), tipo_endereco="COMERCIAL", principal=True, ativo=True,
            )
            db.session.add(novo_endereco)
            db.session.flush()
            novo_restaurante.address_id = novo_endereco.id
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Empresa e endereço criados com sucesso!",
                "dados": {
                    "restaurante": novo_restaurante.to_dict(),
                    "endereco": novo_endereco.to_dict(),
                    "token": TokenService.gerar_token("BUSINESS", novo_restaurante.id, novo_restaurante.email),
                },
            }
        except ValueError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 400}
        except IntegrityError:
            db.session.rollback()
            return {"success": False, "erro": "CNPJ, e-mail ou telefone já cadastrado.", "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar empresa e endereço.", "status_code": 500}

    @staticmethod
    def atualizar_restaurante(restaurante_id, nome=None, email=None):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            if nome is not None:
                restaurante.nome = nome
            if email is not None:
                email_normalizado = email.strip().lower()
                if email_esta_em_uso(email_normalizado, restaurante_id_ignorar=restaurante.id):
                    return {"success": False, "erro": "E-mail já cadastrado em outra conta.", "status_code": 409}
                restaurante.email = email_normalizado
            db.session.commit()
            return {"success": True, "mensagem": "Restaurante atualizado com sucesso!", "dados": restaurante.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar restaurante.", "status_code": 500}

    @staticmethod
    def buscar_configuracao(restaurante_id):
        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            endereco = db.session.get(Endereco, restaurante.address_id) if restaurante.address_id else None
            # Recupera endereço de cadastros legados que não preencheram address_id.
            if endereco is None:
                endereco = Endereco.query.filter_by(id_restaurante=restaurante.id).order_by(
                    Endereco.principal.desc(), Endereco.id.asc()
                ).first()
            return {
                "success": True,
                "mensagem": "Configuração do restaurante carregada.",
                "dados": {"restaurante": restaurante.to_dict(), "endereco": endereco.to_dict() if endereco else None},
            }
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar a configuração do restaurante.", "status_code": 500}

    @staticmethod
    def atualizar_configuracao(restaurante_id, dados):
        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}

            campos_restaurante = (
                "nome", "razao_social", "nome_responsavel", "descricao",
                "valor_minimo_pedido", "taxa_entrega_base", "taxa_entrega_por_km",
                "raio_entrega_km", "horario_funcionamento",
            )
            for campo in campos_restaurante:
                if campo not in dados:
                    continue
                valor = dados[campo]
                if campo in {"taxa_entrega_base", "taxa_entrega_por_km"}:
                    valor = RestauranteService._validar_valor_nao_negativo(valor if valor not in (None, "") else 0, campo)
                elif campo == "raio_entrega_km":
                    valor = RestauranteService._validar_raio(valor)
                setattr(restaurante, campo, valor)

            endereco_dados = dados.get("endereco")
            endereco = db.session.get(Endereco, restaurante.address_id) if restaurante.address_id else None
            if endereco is None:
                endereco = Endereco.query.filter_by(id_restaurante=restaurante.id).order_by(
                    Endereco.principal.desc(), Endereco.id.asc()
                ).first()

            if endereco_dados is not None:
                endereco_novo = endereco is None
                if endereco is None:
                    endereco = Endereco(
                        id_restaurante=restaurante.id, tipo_endereco="COMERCIAL",
                        principal=True, ativo=True,
                    )
                    db.session.add(endereco)

                campos_endereco = (
                    "cep", "rua", "numero", "complemento", "bairro", "cidade",
                    "estado", "referencia", "latitude", "longitude",
                )
                for campo in campos_endereco:
                    if campo in endereco_dados:
                        setattr(endereco, campo, endereco_dados[campo])

                if endereco_novo:
                    obrigatorios = ("cep", "rua", "numero", "bairro", "cidade", "estado")
                    ausentes = [campo for campo in obrigatorios if not str(getattr(endereco, campo, "") or "").strip()]
                    if ausentes:
                        raise ValueError(
                            "Preencha os campos obrigatórios do endereço comercial: " + ", ".join(ausentes)
                        )
                    # Não envie INSERT com colunas NOT NULL vazias: preencha antes do flush.
                    db.session.flush()
                    restaurante.address_id = endereco.id
                elif endereco is not None and not restaurante.address_id:
                    restaurante.address_id = endereco.id

            db.session.commit()
            return {
                "success": True,
                "mensagem": "Configuração do restaurante atualizada com sucesso!",
                "dados": {"restaurante": restaurante.to_dict(), "endereco": endereco.to_dict() if endereco else None},
            }
        except IntegrityError:
            db.session.rollback()
            return {"success": False, "erro": "Os dados informados já estão em uso.", "status_code": 409}
        except (TypeError, ValueError) as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc) or "Existem dados inválidos na configuração.", "status_code": 400}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar a configuração do restaurante.", "status_code": 500}

    @staticmethod
    def atualizar_status_operacional(restaurante_id, status):
        """Atualiza ABERTO/FECHADO; não permite que o parceiro aprove a própria loja."""
        if not isinstance(status, str):
            return {"success": False, "erro": "Informe o status ABERTO ou FECHADO.", "status_code": 400}
        novo_status = status.strip().upper()
        if novo_status not in {"ABERTO", "FECHADO"}:
            return {"success": False, "erro": "O status operacional deve ser ABERTO ou FECHADO.", "status_code": 400}
        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            if restaurante.status not in {"ABERTO", "FECHADO"}:
                return {
                    "success": False,
                    "erro": "A loja ainda não está liberada para abrir ou fechar. Consulte a administração.",
                    "status_code": 409,
                }
            restaurante.status = novo_status
            db.session.commit()
            return {"success": True, "mensagem": "Status da loja atualizado com sucesso.", "dados": {"id": restaurante.id, "status": restaurante.status}}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar o status da loja.", "status_code": 500}

    @staticmethod
    def deletar_restaurante(restaurante_id):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            db.session.delete(restaurante)
            db.session.commit()
            return {"success": True, "mensagem": "Restaurante removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover restaurante.", "status_code": 500}

    @staticmethod
    def listar_produtos_restaurante(restaurante_id, incluir_estoque=False):
        from app.models.product import Produto
        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            produtos = Produto.query.filter_by(restaurant_id=restaurante_id).order_by(Produto.id).all()
            return {
                "success": True,
                "mensagem": "Produtos do restaurante:",
                "dados": [produto.to_dict() if incluir_estoque else produto.to_catalog_dict() for produto in produtos],
            }
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}
