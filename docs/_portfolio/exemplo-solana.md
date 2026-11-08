---
layout: project
title: "Solana — Anchor + CPI"
description: "Programa Anchor que agenda uma query no oracle via CPI e valida o callback com a cb_authority lida da PDA de config."
tags: [exemplo, Solana, Anchor, Rust, CPI, PDA, oracle, ed25519, tutorial]
image: "/img/portfolio/exemplo-solana.svg"
category: exemplo
order: 12
custom_css: "/css/syntax.css"
code_highlight: true
---

## O que este exemplo faz

O programa **`example_consumer`** reproduz na Solana o mesmo fluxo do exemplo
EVM: `request_price` agenda a query ETH/USD via **CPI** (Cross-Program
Invocation) para o programa `rapport_oracle`, e o `__callback` recebe o
resultado validado contra a **`cb_authority`** lida da PDA `config` do oracle.

> Código-fonte real:
> [`contracts/solana/programs/example_consumer/src/lib.rs`](https://github.com/RapportTecnologia/rapport_oracle/blob/main/contracts/solana/programs/example_consumer/src/lib.rs)

## Por que Solana é diferente

Na Solana não existe "storage do contrato" nem `msg.sender`: o estado vive em
**accounts** (aqui, PDAs) e a autoria vem de **signers** passados explicitamente.
O SDK `rapport_oracle_sdk` esconde a complexidade — três helpers bastam:
`read_config`, `cpi_request_accounts`/`rapport_oracle_query` e
`require_cb_authority`.

## Passo 1 — Estado em uma PDA

```rust
use anchor_lang::prelude::*;
use rapport_oracle_sdk::{require_cb_authority, read_config, OracleConfig};

declare_id!("8wpztkqU6h1SX2efUqdTSxpjKiH6KGSZgMnqbVYCQ6jg");

/// Seeds do estado de preço do exemplo.
pub const PRICE_SEED: &[u8] = b"price";

#[account]
#[derive(InitSpace)]
pub struct PriceState {
    pub authority: Pubkey,        // dono do consumidor
    pub oracle_program: Pubkey,   // programa oracle utilizado
    pub price_cents: u64,         // último preço em centavos (result * 10^2)
    pub last_query_id: [u8; 32],  // rqid do último callback
    pub last_updated: i64,        // timestamp do último callback
    pub bump: u8,                 // bump da PDA (valida seeds no callback)
}
```

`initialize` cria a PDA `["price"]` e grava o endereço do programa oracle — a
mesma ideia do `setConnector` da EVM, só que guardado em uma account.

## Passo 2 — Agendar a query via CPI

```rust
    pub fn request_price(ctx: Context<RequestPrice>) -> Result<()> {
        // Lê a config do oracle (valida que oracle_config é a PDA certa)
        let cfg = read_config(&ctx.accounts.oracle_config.to_account_info())?;

        // Monta o CPI: programa alvo + accounts no formato esperado
        let cpi_program = ctx.accounts.oracle_program.to_account_info();
        let cpi_accounts = rapport_oracle_sdk::cpi_request_accounts(
            ctx.accounts.oracle_config.to_account_info(),
            ctx.accounts.query_account.to_account_info(),
            ctx.accounts.authority.to_account_info(),
            ctx.accounts.system_program.to_account_info(),
        );
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);

        // A query em si: delay 0, datasource "URL", arg json(...).USD
        rapport_oracle_sdk::rapport_oracle_query(
            cpi_ctx,
            0,
            "URL".to_string(),
            vec!["json(https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD).USD".to_string()],
        )?;
        let _ = cfg;
        emit!(PriceRequested { requester: ctx.accounts.authority.key() });
        Ok(())
    }
```

O `rqid` é derivado pelo oracle a partir de `requester + nonce` e fica gravado
na PDA `query_account` criada pelo próprio CPI — é ela que o middleware observa
ao fazer `getProgramAccounts`/polling de logs.

## Passo 3 — Callback validado pela `cb_authority`

```rust
    pub fn __callback(ctx: Context<Callback>, query_id: [u8; 32], result: String, proof: Vec<u8>) -> Result<()> {
        let config = read_config(&ctx.accounts.oracle_config.to_account_info())?;
        // Exige que o signer seja o relayer oficial do oracle
        require_cb_authority(&ctx.accounts.oracle_signer, &config)?;

        let st = &mut ctx.accounts.state;
        st.price_cents = rapport_oracle_sdk::parse_int_scaled(&result, 2)
            .ok_or(ConsumerError::BadResult)? as u64;
        st.last_query_id = query_id;
        st.last_updated = Clock::get()?.unix_timestamp;
        let _ = proof;
        emit!(PriceUpdated { query_id, price_cents: st.price_cents });
        Ok(())
    }
```

Equivalente direto da EVM:

| EVM | Solana/Anchor |
|---|---|
| `msg.sender == rapport_oracle_cbAddress()` | `require_cb_authority(&oracle_signer, &config)` |
| `parseInt(_result, 2)` | `parse_int_scaled(&result, 2)` |
| `block.timestamp` | `Clock::get()?.unix_timestamp` |
| `emit Event(...)` | `emit!(Event {...})` |

## Passo 4 — Accounts do callback

```rust
#[derive(Accounts)]
pub struct Callback<'info> {
    /// PDA `config` do oracle — desserializada por `read_config`.
    /// CHECK: o signer é validado contra ela.
    pub oracle_config: UncheckedAccount<'info>,
    /// Relayer do oracle — deve ser igual a `config.cb_authority`.
    pub oracle_signer: Signer<'info>,
    #[account(mut, seeds = [PRICE_SEED], bump = state.bump)]
    pub state: Account<'info, PriceState>,
}
```

Três defesas em camadas: `seeds`/`bump` garantem que `state` é a PDA certa,
`read_config` garante que `oracle_config` é a config do oracle, e
`require_cb_authority` amarra o signer ao relayer — a prova ed25519 em `proof`
fica disponível para auditoria adicional.

## Testando

```bash
anchor build
anchor keys sync   # sincroniza declare_id! com os keypairs
anchor deploy --provider.cluster devnet
```

Em seguida, invoque `request_price` pelo client (TS) e observe o evento
`PriceRequested`; o middleware (polling via `getProgramAccounts`) devolve o
`__callback` no tick seguinte.
