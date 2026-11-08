---
layout: project
title: "EVM — Múltiplas Consultas"
description: "Como emitir várias queries de uma vez e despachar cada resposta ao seu propósito usando o rqid como chave."
tags: [exemplo, EVM, Solidity, oracle, multi-query, rqid, dispatch, mapping, tutorial]
image: "/img/portfolio/exemplo-multiquery.svg"
category: exemplo
order: 11
custom_css: "/css/syntax.css"
code_highlight: true
---

## O que este exemplo faz

O **`MultiQueryExample`** emite três consultas de uma só vez (ETH/USD, BTC/USD
e EUR/USD) e mostra o padrão essencial para qualquer consumidor não trivial:
**associar cada `rqid` a um propósito** e despachar o resultado correto quando
o `__callback` chegar — os callbacks podem chegar fora de ordem.

> Código-fonte real:
> [`contracts/evm/examples/MultiQueryExample.sol`](https://github.com/RapportTecnologia/rapport_oracle/blob/main/contracts/evm/examples/MultiQueryExample.sol)

## O problema que o rqid resolve

Diferente do exemplo anterior (uma query por vez), aqui há várias requisições
pendentes simultaneamente. Quando o relayer chama `__callback(_queryId, ...)`,
como saber se o resultado é do ETH ou do BTC? Resposta: um `mapping` de
`rqid → propósito`.

## Passo 1 — Modelar os propósitos

```solidity
contract MultiQueryExample is usingRapportOracle {
    enum Purpose {
        EthUsd,
        BtcUsd,
        EurUsd
    }

    /// Propósito associado a cada rqid pendente.
    mapping(bytes32 => Purpose) public purposeOf;
    /// Últimos resultados crus por propósito (índice = uint8(Purpose)).
    string[3] public lastResult;

    event QueryRegistered(bytes32 indexed queryId, Purpose purpose);
    event ResultArrived(bytes32 indexed queryId, Purpose purpose, string result);
```

- `Purpose` enumera o que cada query significa para a aplicação;
- `purposeOf` é o "dispatcher": a ponte entre o `rqid` opaco e a intenção;
- `lastResult` indexado por `uint8(purpose)` guarda o último valor de cada um.

## Passo 2 — Emitir as três queries

```solidity
    function requestAll() public returns (bytes32[3] memory rqids) {
        string memory base = "json(https://min-api.cryptocompare.com/data/price?fsym=";
        string memory tail = "&tsyms=USD).USD";

        rqids[0] = _register(rapport_oracle_query(0, "URL", strConcat(base, "ETH", tail)), Purpose.EthUsd);
        rqids[1] = _register(rapport_oracle_query(0, "URL", strConcat(base, "BTC", tail)), Purpose.BtcUsd);
        rqids[2] = _register(rapport_oracle_query(0, "URL", strConcat(base, "EUR", tail)), Purpose.EurUsd);
    }
```

Detalhes didáticos:

- `strConcat` (helper da lib, 2–5 argumentos) monta a datasource sem custo de
  manipulação manual de bytes — a mesma URL base serve aos três ativos;
- `delay = 0`: todas disparam no próximo tick do cron (~1 min);
- `_register` encapsula o registro do propósito e o evento de auditoria:

```solidity
    function _register(bytes32 rqid, Purpose purpose) internal returns (bytes32) {
        purposeOf[rqid] = purpose;
        emit QueryRegistered(rqid, purpose);
        return rqid;
    }
```

## Passo 3 — Despachar no callback

```solidity
    function __callback(bytes32 _queryId, string memory _result, bytes memory _proof) public override {
        require(msg.sender == rapport_oracle_cbAddress(), "Apenas oracle da rapport pode usar esta funcao");
        _proof;
        Purpose purpose = purposeOf[_queryId];
        lastResult[uint8(purpose)] = _result;
        delete purposeOf[_queryId];
        emit ResultArrived(_queryId, purpose, _result);
    }
```

A leitura é direta:

1. `_queryId` identifica qual query foi respondida;
2. `purposeOf[_queryId]` recupera o propósito registrado no passo anterior;
3. O resultado vai para o slot correto de `lastResult`;
4. `delete purposeOf[_queryId]` libera o storage (refund de gas) e marca a
   requisição como atendida.

## Padrões que este exemplo habilita

- **Painéis multi-ativo**: feeds de N moedas/tokens com um callback só;
- **Queries compostas**: preço + timestamp + fonte, cada uma com propósito;
- **Timeout e retry**: se `purposeOf[rqid]` continuar setado após um prazo,
  sua aplicação pode reemitir a query com segurança.

## Pontos de atenção

- **`enum` default `0`**: uma `rqid` desconhecida lê `Purpose.EthUsd`. Para
  blindar, comece o enum em `None` ou valide com um mapping separado de "existe".
- **Custo de storage**: cada pendência é um slot de mapping — limpe-as no
  callback (como feito com `delete`) e considere prazos de expiração.
- **Fora de ordem é normal**: o middleware resolve queries de forma assíncrona;
  nunca assuma que o callback N chega depois do N−1.
