---
layout: project
title: "Stellar — Soroban (Rust)"
description: "Contrato Soroban no_std que agenda a query no conector e valida o callback com require_cb_address da lib."
tags: [exemplo, Stellar, Soroban, Rust, no_std, oracle, ed25519, tutorial]
image: "/img/portfolio/exemplo-stellar.svg"
category: exemplo
order: 13
custom_css: "/css/syntax.css"
code_highlight: true
---

## O que este exemplo faz

O **`ExampleConsumer`** é a versão Stellar/Soroban do fluxo canônico:
`update()` agenda a query `json(<url>).USD` no conector `rapport-oracle` e o
`__callback` grava o resultado após validar o `caller` contra o `cb_address`
lido do oracle — tudo em Rust `no_std` sobre o Soroban SDK.

> Código-fonte real:
> [`contracts/stellar/example-consumer/src/lib.rs`](https://github.com/RapportTecnologia/rapport_oracle/blob/main/contracts/stellar/example-consumer/src/lib.rs)

## O modelo Soroban em 30 segundos

- **Sem `msg.sender`**: quem invoca é explicitado por parâmetro (`caller`) e
  autenticado com `require_auth`;
- **Storage tipado**: o estado vive em `env.storage()` sob chaves de um enum;
- **`String`/`Vec` do SDK**: não há `std` — use `String::from_str(&env, ...)`
  e `vec![&env, ...]`.

## Passo 1 — Storage e inicialização

```rust
#![no_std]

use rapport_oracle_lib as oracle;
use soroban_sdk::{contract, contractimpl, contracterror, contracttype, symbol_short, vec, Address, Bytes, BytesN, Env, String};

/// Chaves de storage do exemplo.
#[contracttype]
pub enum DataKey {
    Oracle,
    Admin,
    PriceCents,
    LastQueryId,
    LastUpdated,
}

#[contract]
pub struct ExampleConsumer;

#[contractimpl]
impl ExampleConsumer {
    /// Inicializa com o endereço do conector oracle (admin autentica).
    pub fn initialize(env: Env, admin: Address, oracle_addr: Address) {
        if env.storage().instance().has(&DataKey::Oracle) {
            panic!("already initialized");
        }
        admin.require_auth();
        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage().instance().set(&DataKey::Oracle, &oracle_addr);
    }
```

`DataKey::Oracle` guarda o conector — o equivalente ao `setConnector` da EVM,
persistido no instance storage do contrato.

## Passo 2 — Agendar a query

```rust
    /// Agenda a consulta do preço ETH/USD e retorna o `rqid`.
    pub fn update(env: Env) -> BytesN<32> {
        let oracle_addr: Address = env.storage().instance().get(&DataKey::Oracle).unwrap();
        let requester = env.current_contract_address();
        let rqid = oracle::rapport_oracle_query(
            &env,
            &oracle_addr,
            &requester,
            600,                                  // delay em segundos
            String::from_str(&env, "URL"),        // datasource
            vec![
                &env,
                String::from_str(&env,
                    "json(https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD).USD"),
            ],
        );
        env.storage().instance().set(&DataKey::LastQueryId, &rqid);
        env.events().publish((symbol_short!("query"), rqid.clone()), ());
        rqid
    }
```

O `requester` é o **próprio contrato** — a autoria do invocador original
propaga via `require_auth` dentro do conector. O `rqid` volta como
`BytesN<32>` e vai tanto para o storage quanto para um evento indexado.

## Passo 3 — Callback com `require_cb_address`

```rust
    /// Callback do oracle — exige `caller` igual ao `cb_address` do conector.
    pub fn __callback(env: Env, caller: Address, query_id: BytesN<32>, result: String, proof: Bytes) -> Result<(), ConsumerError> {
        let oracle_addr: Address = env.storage().instance().get(&DataKey::Oracle).ok_or(ConsumerError::NotInitialized)?;
        // Reverte se `caller` não for o relayer oficial
        oracle::require_cb_address(&env, &caller, &oracle_addr);

        let cents = oracle::parse_int_scaled(&env, &result, 2).ok_or(ConsumerError::BadResult)?;
        env.storage().instance().set(&DataKey::PriceCents, &cents);
        env.storage().instance().set(&DataKey::LastUpdated, &env.ledger().timestamp());
        env.events().publish(
            (symbol_short!("price"), query_id),
            (cents, proof.len()),
        );
        Ok(())
    }
```

O paralelo com as outras chains:

| EVM | Stellar/Soroban |
|---|---|
| `msg.sender == rapport_oracle_cbAddress()` | `oracle::require_cb_address(&env, &caller, &oracle_addr)` |
| `parseInt(_result, 2)` | `oracle::parse_int_scaled(&env, &result, 2)` |
| `block.timestamp` | `env.ledger().timestamp()` |
| `emit PriceUpdated(...)` | `env.events().publish((topic), (data))` |

Note que o `caller` é parâmetro explícito — o relayer se identifica e a lib
confirma, on-chain, que ele é o `cb_address` registrado no conector.

## Erros tipados

```rust
#[contracterror]
#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum ConsumerError {
    NotInitialized = 1,  // callback antes do initialize
    NotAdmin = 2,
    BadResult = 3,       // resultado não numérico
}
```

## Build e deploy

```bash
cargo build --target wasm32v1-none --release
# wasm em target/wasm32v1-none/release/example_consumer.wasm
stellar contract deploy --wasm <wasm> --network testnet
stellar contract invoke --id <contract> -- initialize --admin <G...> --oracle_addr <C...>
stellar contract invoke --id <contract> -- update
```

Depois do `update`, o middleware (polling de `getEvents` na testnet) devolve o
`__callback` com o preço em centavos — consulte com `price_cents`.
