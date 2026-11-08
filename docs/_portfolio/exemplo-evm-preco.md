---
layout: project
title: "EVM — Preço ETH/USD"
description: "O exemplo canônico: um contrato Solidity que agenda uma consulta ao preço ETH/USD e recebe o resultado via callback assinado."
tags: [exemplo, EVM, Solidity, oracle, callback, parseInt, datasource URL, tutorial]
image: "/img/portfolio/exemplo-evm.svg"
category: exemplo
order: 10
custom_css: "/css/syntax.css"
code_highlight: true
---

## O que este exemplo faz

O contrato **`EthUsdPrice`** é o "Hello World" do Rapport Oracle: ao chamar
`update()`, ele agenda uma consulta ao preço ETH/USD na API pública da
CryptoCompare e, alguns instantes depois, o middleware devolve o valor no
`__callback` — exatamente o fluxo clássico do Oraclize/Provable.

> Código-fonte real:
> [`contracts/evm/examples/EthUsdPrice.sol`](https://github.com/RapportTecnologia/rapport_oracle/blob/main/contracts/evm/examples/EthUsdPrice.sol)

## Passo 1 — Importar e herdar a biblioteca

```solidity
// SPDX-License-Identifier: CC-BY-SA-4.0
pragma solidity ^0.8.24;

import {usingRapportOracle} from "../lib/rapportOracle.sol";
// No Remix, importe direto do GitHub:
// import "github.com/rapporttecnologia/rapport_oracle/contracts/evm/lib/rapportOracle.sol";

contract EthUsdPrice is usingRapportOracle {
```

A lib `usingRapportOracle` é **self-contained** (sem imports externos) e já
entrega: `rapport_oracle_query`, `rapport_oracle_cbAddress`, helpers de parse
(`parseInt`, `strConcat`, `uint2str`...) e o contrato `__callback` a ser
sobrescrito.

## Passo 2 — Estado e resolução do conector

```solidity
    /// Preço ETH/USD escalado por 100 (ex.: 312345 = US$ 3.123,45).
    uint256 public ethUsd;
    bytes32 public lastQueryId;
    uint256 public lastUpdated;

    event QueryScheduled(bytes32 indexed queryId, string datasource, string arg);
    event PriceUpdated(bytes32 indexed queryId, uint256 priceCents, string rawResult);

    constructor(address connector) {
        if (connector != address(0)) {
            rapport_oracle_setConnector(connector);
        }
    }
```

Dois pontos importantes:

- **Escalamento**: Solidity não tem ponto flutuante — guardamos o preço em
  centavos (`312345` = US$ 3.123,45). É sua responsabilidade definir a escala.
- **Conector automático**: na Polygon Amoy (`chainId 80002`) a lib já conhece o
  conector oficial `0x28A5...1a29` e o constructor pode receber `address(0)`.
  Em outras redes, passe o endereço do `RapportOracle` deployado.

## Passo 3 — Agendar a query

```solidity
    function update() public returns (bytes32 rqid) {
        rqid = rapport_oracle_query(
            60 * 10,              // delay mínimo: 10 minutos
            "URL",                // datasource v1
            "json(https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD,EUR,GBP).USD"
        );
        lastQueryId = rqid;
        emit QueryScheduled(rqid, "URL", "cryptocompare.USD");
    }
```

Anatomia dos argumentos:

| Parâmetro | Valor | Significado |
|---|---|---|
| `delay` | `600` | Segundos mínimos até a execução off-chain (granularidade ~1 min no middleware v1; `0` = imediato) |
| `datasource` | `"URL"` | Única fonte da v1: um GET HTTP |
| `arg` | `json(<url>).USD` | DSL: faz o GET e extrai o campo `USD` do JSON |

A string `json(<endpoint>).<path>` é interpretada pelo resolver do Worker:
`{ETH: {USD: 3123.45, ...}}` → retorna `"3123.45"`. Guarde o `rqid`
retornado — é ele que identifica sua requisição no callback.

## Passo 4 — Receber o resultado no `__callback`

```solidity
    function __callback(bytes32 _queryId, string memory _result, bytes memory _proof) public override {
        require(
            msg.sender == rapport_oracle_cbAddress(),
            "Apenas oracle da rapport pode usar esta funcao"
        );
        _proof; // prova disponível p/ verificação extra via RapportOracle.verifyProof
        ethUsd = parseInt(_result, 2);
        lastUpdated = block.timestamp;
        emit PriceUpdated(_queryId, ethUsd, _result);
    }
}
```

Três obrigações de todo `__callback`:

1. **`override`** — a assinatura vem da base `usingRapportOracle`;
2. **Validar o remetente** — só o `cbAddress` (relayer) pode invocar, senão
   qualquer um injeta preço falso;
3. **Parse do resultado** — `_result` chega como string (`"3123.45"`) e
   `parseInt(_result, 2)` converte para inteiro escalado (`312345`).

## O que acontece depois do `update()`

1. O conector emite `LogNewQuery` com sua query;
2. O Worker (cron 1 min) lê o evento, aguarda o `delay`, faz o GET e extrai `.USD`;
3. O relayer assina `keccak256(qid, result, consumer)` e chama `__callback`;
4. `ethUsd`, `lastUpdated` e o evento `PriceUpdated` registram a resposta.

## Variações para experimentar

- **Outro campo do mesmo JSON**: troque `.USD` por `.EUR` para EUR/ETH.
- **Delay zero**: `rapport_oracle_query(0, ...)` para resposta no próximo tick.
- **Prova adicional**: chame `RapportOracle(connector).verifyProof(...)` para
  auditar a assinatura ECDSA do relayer dentro do callback.
- **Helpers úteis**: `strcmp`, `indexOf`, `substring` e `parseTimestamp`
  (datas ISO-8601 → unix) já estão na lib.
