#!/usr/bin/env python3
"""
Author:  Carlos Delfino
Email:   consultoria@carlosdelfino.eti.br
WhatsApp: +55 (85) 98520-5490

Gera o payload Pix "copia e cola" (BR Code / EMVCo) e o QR Code em PNG usados
na secao de doacao dos READMEs do monorepo Rapport Oracle.

O QR Code estatico segue o Manual de Padroes para Iniciacao do Pix (BCB):
chave = CNPJ do recebedor, valor livre (campo 54 omitido) e mensagem fixa
(campo 26/02) que indica a destinacao da doacao. O txid (campo 62/05) usa
apenas alfanumericos, conforme o padrao BR Code.

Usage:
    python3 scripts/generate_pix_qrcode.py

Requires:
    qrcode[pil]  (pip install "qrcode[pil]")

Outputs:
    <repo>/<modulo>/docs/assets/pix-doacao-qrcode.png  para cada modulo
    listado em MODULES, e imprime o payload "copia e cola" no stdout para
    conferencia/embbeding manual nos READMEs.
"""

import binascii
from pathlib import Path

import qrcode

# Chave Pix CNPJ 67.904.299/0001-80 (BR Code exige somente digitos).
PIX_KEY = "67904299000180"

# Nome do recebedor exibido no app do banco (campo 59, max. 25 caracteres).
MERCHANT_NAME = "RAPPORT TECNOLOGIA"

# Cidade do recebedor (campo 60, max. 15 caracteres).
MERCHANT_CITY = "FORTALEZA"

# Mensagem/descricao embutida no QR (campo 26/02, max. 40 caracteres):
# indica que a doacao mantem as APIs e servidores do projeto.
DESCRIPTION = "DOACAO APIS E SERVIDORES RAPPORT ORACLE"

# txid do campo 62/05: apenas [a-zA-Z0-9], max. 25 caracteres.
TXID = "DOACAORAPPORTORACLE"

# Modulos do monorepo que recebem o PNG em docs/assets/.
MODULES = ("middleware", "smartcontracts")

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_NAME = "pix-doacao-qrcode.png"


def emv(field_id: str, value: str) -> str:
    """
    Codifica um campo no formato EMV (ID + tamanho em 2 digitos + valor).

    Args:
        field_id: Identificador de 2 digitos do campo (ex.: "26").
        value: Conteudo do campo.

    Returns:
        String "IDLLvalor" pronta para concatenacao no payload.
    """
    return f"{field_id}{len(value):02d}{value}"


def crc16(payload: str) -> str:
    """
    Calcula o CRC16-CCITT-FALSE exigido pelo campo 63 do BR Code.

    Args:
        payload: Payload completo ja terminado em "6304".

    Returns:
        CRC em hexadecimal maiusculo com 4 digitos.
    """
    return f"{binascii.crc_hqx(payload.encode('utf-8'), 0xFFFF):04X}"


def build_payload() -> str:
    """
    Monta o payload Pix "copia e cola" estatico (reutilizavel, valor livre).

    Returns:
        String BR Code completa, incluindo o CRC16 final.
    """
    merchant_account = (
        emv("00", "br.gov.bcb.pix")
        + emv("01", PIX_KEY)
        + emv("02", DESCRIPTION)
    )
    additional_data = emv("05", TXID)
    payload = (
        emv("00", "01")              # Payload Format Indicator
        + emv("01", "11")            # Estatico: QR reutilizavel
        + emv("26", merchant_account)
        + emv("52", "0000")          # Merchant Category Code (nao categorizado)
        + emv("53", "986")           # Moeda: BRL
        + emv("58", "BR")            # Pais
        + emv("59", MERCHANT_NAME)
        + emv("60", MERCHANT_CITY)
        + emv("62", additional_data)
        + "6304"
    )
    return payload + crc16(payload)


def main() -> None:
    """
    Gera o payload, salva o PNG em docs/assets de cada modulo e imprime o
    "copia e cola" para conferencia.
    """
    payload = build_payload()
    image = qrcode.make(payload, box_size=10, border=4)
    for module in MODULES:
        target = REPO_ROOT / module / "docs" / "assets" / ASSET_NAME
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target)
        print(f"QR Code salvo em {target}")
    print(f"\nPix copia e cola:\n{payload}\n")


if __name__ == "__main__":
    main()
