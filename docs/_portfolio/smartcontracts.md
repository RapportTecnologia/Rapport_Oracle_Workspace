---
layout: project
title: "Smart Contracts"
description: "Conectores on-chain do oracle para EVM/Polygon, Solana e Stellar, com bibliotecas para desenvolvedores e exemplos de consumidores."
tags: [smart contracts, Solidity, Anchor, Soroban, EVM, Polygon, Solana, Stellar, oracle, Hardhat, Foundry, Safe multisig]
image: "smartcontracts.svg"
---

## O que são os Smart Contracts

O módulo **smartcontracts** contém os conectores on-chain do Rapport Oracle — contratos e programas que recebem `query(delay, datasource, arg)`, emitem o evento de nova query e validam o `__callback` do relayer — além de bibliotecas prontas para desenvolvedores e exemplos de contratos consumidores.

## Por chain

| Chain | Stack | Artefatos |
|---|---|---|
| **EVM / Polygon** | Solidity `^0.8.24`, Hardhat + Foundry | `RapportOracle.sol`, lib `usingRapportOracle`, exemplos e mocks |
| **Solana** | Anchor (Rust) | Programa `rapport_oracle` com PDA por query + SDK `rapport_oracle_sdk` |
| **Stellar** | Soroban (Rust) | Contrato `rapport-oracle` (`BytesN<32>` + evento) + crate `rapport-oracle-lib` |

## Segurança

- Ownership administrativo em **duas etapas**, sob multisig **Safe 2-de-3** já na testnet.
- `cbAddress`/relayer operacional **sem privilégios administrativos**.
- `__callback` exige `msg.sender == rapport_oracle_cbAddress()`.
- Testes unitários, de integração e fuzz (Forge) por requisito — ver `docs/REQUIREMENTS.md`.

## Deploys e utilitários

- Deploy em **Polygon Amoy** registrado em `deployments/polygonAmoy.json`.
- `npm run check:balance:net -- "Polygon Amoy"` consulta saldos das carteiras por nome/chainId de rede (EVM) ou cluster (Solana) — tutorial em `docs/query-balances.md`.

## Repositório

Código-fonte, tutoriais por chain e checklist de segurança em
[github.com/RapportTecnologia/rapport_oracle](https://github.com/RapportTecnologia/rapport_oracle).
