# Documentação técnica do CandyLand

Este arquivo é a porta de entrada para a documentação criada na revisão de **14/11/2026**.

- [Índice geral da documentação](docs/INDICE.md)
- [Mapa de pastas e arquivos](docs/estrutura/README.md)
- [Auditoria técnica, pendências e plano de integração](docs/auditoria-projeto-e-plano-integracao-2026-11-14.md)
- [Registro da remoção dos controladores duplicados](docs/registro-remocao-controladores-duplicados.md)

## Visão rápida

O repositório contém três aplicações/camadas principais: API Flask em `backend/`, aplicação web React/Vite em `frontend/` e aplicativo Android nativo Kotlin em `mobile/`. A pasta `docs/` reúne decisões, requisitos, relatórios de validação e materiais de configuração; `scripts/` contém automações de apoio ao desenvolvimento no Windows.

## Estado desta documentação

O conteúdo foi produzido por inspeção estática da branch `main` em 14/11/2026 e da diferença entre `main` e `dev`. A inspeção não substitui execução local de testes, builds, nem validação de credenciais ou integrações externas. O script `aplicar.ps1` que acompanha o pacote cria a branch documental no clone local, copia os arquivos, remove a pasta redundante de controladores após validar o conteúdo esperado e gera um commit.
