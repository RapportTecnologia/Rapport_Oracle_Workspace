![header](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=Rapport%20Oracle%20Workspace&fontSize=36&fontAlignY=35&animation=twinkling)

![visitors](https://visitor-badge.laobi.icu/badge?page_id=RapportTecnologia.AgenticSpace.workspace_readme)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-blue.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
![Language: Portuguese](https://img.shields.io/badge/Language-Portuguese-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Ongoing-yellow)
[![GitHub Issues](https://img.shields.io/github/issues/RapportTecnologia/AgenticSpace)](https://github.com/RapportTecnologia/AgenticSpace/issues)

# Rapport Oracle Workspace

Workspace raiz do projeto **Rapport Oracle** — um oráculo multi-chain
(EVM/Polygon, Solana e Stellar) com middleware em Cloudflare Workers.
Os módulos são mantidos em repositórios próprios e integrados aqui como
**git submodules**, de modo que cada um preserva histórico, issues e
pipelines independentes.

## Estrutura do workspace

| Módulo | Tipo | Repositório remoto | Descrição |
|---|---|---|---|
| `middleware/` | submodule | `RapportTecnologia/rapport_oracle_middleware` | Worker Cloudflare que expõe a API do oráculo, cache KV e fila de atualizações. |
| `smartcontracts/` | submodule | `RapportTecnologia/rapport_oracle` | Contratos/programas on-chain (Hardhat/Foundry, Anchor, Soroban) e scripts de deploy. |
| `scripts/` | diretório | — | Utilitários locais do workspace (ex.: geração do QR Code Pix de doação). |
| `.devin/` | diretório | — | Regras e configurações do agente Devin para este workspace. |

## Clonagem

Para clonar o workspace já com os submódulos:

```bash
git clone --recurse-submodules https://github.com/RapportTecnologia/Rapport_Oracle_Workspace.git
```

Se o workspace já foi clonado sem os submódulos:

```bash
git submodule update --init --recursive
```

## Trabalhando com os submódulos

- Cada submódulo aponta para um commit fixo do seu repositório remoto.
  Alterações devem ser feitas dentro do diretório do submódulo, commitadas
  e enviadas ao remoto próprio; depois o workspace registra o novo gitlink.
- Para atualizar todos os submódulos para o `main` remoto:

  ```bash
  git submodule update --remote --merge
  ```

- Convenções de branch e commit seguem `.devin/rules/git.md`
  (Conventional Branch 1.1.0 + Conventional Commits 1.0.0-beta.4).

## Configuração de ambiente

- Copie `.env.example` para `.env` e preencha as chaves de
  testnet/devnet. `.env` **nunca** deve ser commitado (já está no
  `.gitignore`).
- Cada submódulo possui seu próprio arquivo de variáveis
  (`.env` / `.dev.vars`); consulte o README de cada módulo.

## Segurança

- Chaves privadas, tokens e segredos vivem apenas em arquivos `.env`
  locais ou gerenciadores de segredos — nunca em código versionado.
- Commits e PRs passam por revisão seguindo as regras em `.devin/rules/`
  (security, private_key, tests_and_analysis).

## Changelog

| Data | Versão | Descrição |
|---|---|---|
| 2026-11-08 | 0.1.0 | Inicialização do workspace com submódulos `middleware` e `smartcontracts` |

![footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer&animation=twinkling)
