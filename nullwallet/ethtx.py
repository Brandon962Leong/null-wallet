"""Minimal Ethereum legacy (EIP-155) transaction builder / signer, RLP encoder and address derivation. No dependencies."""
from .keccak import keccak256
from . import secp256k1 as ec


def _int_bytes(n: int) -> bytes:
    return b"" if n == 0 else n.to_bytes((n.bit_length() + 7) // 8, "big")


def rlp(x) -> bytes:
    if isinstance(x, int): x = _int_bytes(x)
    if isinstance(x, (bytes, bytearray)):
        b = bytes(x)
        if len(b) == 1 and b[0] < 0x80: return b
        return _len(len(b), 0x80) + b
    if isinstance(x, (list, tuple)):
        body = b"".join(rlp(i) for i in x)
        return _len(len(body), 0xC0) + body
    raise TypeError(type(x))


def _len(n: int, off: int) -> bytes:
    if n < 56: return bytes([off + n])
    lb = _int_bytes(n)
    return bytes([off + 55 + len(lb)]) + lb


def address_of(priv: int) -> str:
    x, y = ec.pubkey(priv)
    return "0x" + keccak256(x.to_bytes(32, "big") + y.to_bytes(32, "big"))[-20:].hex()


def checksum(addr: str) -> str:
    a = addr.lower().replace("0x", ""); h = keccak256(a.encode()).hex()
    return "0x" + "".join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(a))


def sign_legacy(priv: int, nonce: int, gas_price: int, gas_limit: int, to: str, value: int, data: bytes, chain_id: int) -> bytes:
    to_b = bytes.fromhex(to.lower().replace("0x", ""))
    assert len(to_b) == 20, "bad address"
    h = keccak256(rlp([nonce, gas_price, gas_limit, to_b, value, data, chain_id, 0, 0]))
    r, s, rec = ec.sign(priv, h)
    v = rec + 35 + 2 * chain_id
    return rlp([nonce, gas_price, gas_limit, to_b, value, data, v, r, s])


def tx_hash(raw: bytes) -> str:
    return "0x" + keccak256(raw).hex()
