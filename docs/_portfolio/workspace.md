---
layout: project
title: "Workspace"
description: "Repositório raiz que integra os módulos do Rapport Oracle como git submodules, com regras de engenharia e utilitários locais."
tags: [workspace, git submodules, monorepo, Devin rules, Conventional Commits, engenharia]
image: "workspace.svg"
---

## O que é o Workspace

O **Rapport Oracle Workspace** é o repositório raiz do projeto. Ele integra os módulos como **git submodules**, de modo que cada repositório preserva histórico, issues e pipelines independentes.

## Estrutura

| Módulo | Tipo | Descrição |
|---|---|---|
| `middleware/` | submodule | Worker Cloudflare — API do oráculo, cache KV e fila de atualizações |
| `smartcontracts/` | submodule | Contratos/programas on-chain e scripts de deploy |
| `scripts/` | diretório | Utilitários locais (ex.: geração do QR Code Pix de doação) |
| `.devin/` | diretório | Regras do agente Devin para este workspace |

## Clonagem

```bash
git clone --recurse-submodules https://github.com/RapportTecnologia/Rapport_Oracle_Workspace.git
# ou, se já clonado sem os submódulos:
git submodule update --init --recursive
```

## Convenções

- Branches seguem **Conventional Branch 1.1.0** e commits **Conventional Commits 1.0.0-beta.4** (ver `.devin/rules/git.md`).
- Segredos apenas em `.env` local — nunca versionados.

## Repositório

[github.com/RapportTecnologia/Rapport_Oracle_Workspace](https://github.com/RapportTecnologia/Rapport_Oracle_Workspace)
