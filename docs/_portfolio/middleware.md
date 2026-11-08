---
layout: project
title: "Middleware — Cloudflare Worker"
description: "Worker Cloudflare que intermedeia requisições de oracle entre smart contracts e fontes de dados externas, no modelo Oraclize/Provable."
tags: [middleware, Cloudflare Workers, oracle, Provable, Oraclize, KV, cron, TypeScript, resolver, ECDSA, ed25519]
image: "/img/portfolio/middleware.svg"
category: modulo
order: 1
---

## O que é o Middleware

O **middleware** é um Worker Cloudflare que observa os eventos de query emitidos pelos conectores on-chain (EVM, Solana, Stellar), busca o dado na fonte externa indicada e devolve o resultado ao contrato consumidor via `__callback` assinado.

## Componentes

- **`src/index.ts`** — entrypoint com `scheduled` (cron `* * * * *`) e `fetch` (`/health`, `/status`).
- **`src/chains/`** — adapters por chain sobre a interface `OracleChain`, instanciados via Factory.
- **`src/services/orchestrator.ts`** — ciclo coleta → agenda → resolve → callback → checkpoint.
- **`src/services/resolver.ts`** — DSL `json(url).path` com cap de tamanho e timeout no fetch.
- **`src/services/proof.ts`** — prova ECDSA (EVM) / ed25519 (Solana, Stellar).
- **`src/services/state.ts`** — KV `ORACLE_STATE`: checkpoints, pendências e deduplicação.

## API pública

| Endpoint | Descrição |
|---|---|
| `GET /health` | Liveness do Worker |
| `GET /status` | Checkpoint processado e queries pendentes por chain |

Respostas seguem o padrão `{code, message, details, next_step}`.

## Decisões de arquitetura

- **Cron de 1 minuto** — Workers não mantêm WebSocket de escuta; o polling de logs honra `delay` com granularidade de ~1 min (upgrade futuro: Durable Object + alarm).
- **Callback direto ao consumidor** — o relayer chama `__callback` e o consumidor valida `cbAddress` on-chain.
- **Proof v1** — assinatura do relayer sobre `keccak256(qid, result, consumer)`, verificável via `RapportOracle.verifyProof`.

## Repositório

Código-fonte e documentação completa (arquitetura, API e runbook de deploy) em
[github.com/RapportTecnologia/rapport_oracle_middleware](https://github.com/RapportTecnologia/rapport_oracle_middleware).
