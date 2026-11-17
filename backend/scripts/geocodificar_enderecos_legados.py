"""Preenche coordenadas ausentes em endereços já cadastrados.

Execute primeiro sem --execute para conferir quantos endereços serão consultados.
Cada endereço processado pode gerar uma chamada billable ao Google Geocoding API.
"""
from __future__ import annotations

import argparse
import time

from app import create_app
from app.database.database import db
from app.models.address import Endereco
from app.services.geocoding_service import GeocodingService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Localiza endereços antigos sem latitude/longitude usando o Google Geocoding."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executa as consultas e grava as coordenadas. Sem esta opção, apenas mostra a quantidade.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limita a quantidade de endereços nesta execução (0 = todos).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Pausa em segundos entre as consultas (padrão: 0.2).",
    )
    args = parser.parse_args()

    if args.limit < 0 or args.delay < 0:
        parser.error("--limit e --delay não podem ser negativos.")

    application = create_app()
    with application.app_context():
        if not application.config.get("GOOGLE_MAPS_GEOCODING_API_KEY"):
            print(
                "GOOGLE_MAPS_GEOCODING_API_KEY não está configurada em backend/.env. "
                "Nenhuma consulta foi feita."
            )
            return 2

        query = Endereco.query.filter(
            Endereco.ativo.is_(True),
            (Endereco.latitude.is_(None)) | (Endereco.longitude.is_(None)),
        ).order_by(Endereco.id.asc())
        total = query.count()
        if args.limit:
            query = query.limit(args.limit)
        enderecos = query.all()

        print(f"Endereços ativos sem coordenadas: {total}")
        print(f"Selecionados nesta execução: {len(enderecos)}")
        if not args.execute:
            print("Simulação concluída. Use --execute para chamar o Google e gravar os resultados.")
            print("Atenção: cada endereço processado pode gerar custo na Google Maps Platform.")
            return 0

        sucesso = 0
        falha = 0
        for indice, endereco in enumerate(enderecos, start=1):
            resultado = GeocodingService.geocodificar(
                {
                    "cep": endereco.cep,
                    "rua": endereco.rua,
                    "numero": endereco.numero,
                    "bairro": endereco.bairro,
                    "cidade": endereco.cidade,
                    "estado": endereco.estado,
                }
            )
            if resultado["success"]:
                coordenadas = resultado["dados"]
                endereco.latitude = coordenadas["latitude"]
                endereco.longitude = coordenadas["longitude"]
                db.session.commit()
                sucesso += 1
                print(f"[{indice}/{len(enderecos)}] Endereço #{endereco.id}: localizado e salvo.")
            else:
                db.session.rollback()
                falha += 1
                print(
                    f"[{indice}/{len(enderecos)}] Endereço #{endereco.id}: "
                    f"{resultado['erro']}"
                )
                if resultado.get("status_code") == 503:
                    print("O provedor recusou/limitou a consulta. A execução foi interrompida.")
                    break
            if indice < len(enderecos) and args.delay:
                time.sleep(args.delay)

        print(f"Concluído: {sucesso} localizado(s), {falha} pendente(s)/falha(s).")
        return 0 if falha == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
