"""secp256k1 ECDSA (sign / verify / recover) with RFC 6979 deterministic nonces and low-s signatures, pure Python."""
import hashlib, hmac

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _inv(a, m):
    return pow(a, -1, m)


def _add(p, q):
    if p is None: return q
    if q is None: return p
    if p[0] == q[0] and (p[1] + q[1]) % P == 0: return None
    if p == q:
        l = 3 * p[0] * p[0] * _inv(2 * p[1], P) % P
    else:
        l = (q[1] - p[1]) * _inv(q[0] - p[0], P) % P
    x = (l * l - p[0] - q[0]) % P
    return (x, (l * (p[0] - x) - p[1]) % P)


def _mul(k, pt):
    r, add = None, pt
    while k:
        if k & 1: r = _add(r, add)
        add = _add(add, add)
        k >>= 1
    return r


def pubkey(priv: int):
    assert 0 < priv < N
    return _mul(priv, G)


def _rfc6979(priv: int, h: bytes) -> int:
    x = priv.to_bytes(32, "big"); v = b"\x01" * 32; k = b"\x00" * 32
    k = hmac.new(k, v + b"\x00" + x + h, hashlib.sha256).digest(); v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b"\x01" + x + h, hashlib.sha256).digest(); v = hmac.new(k, v, hashlib.sha256).digest()
    while True:
        v = hmac.new(k, v, hashlib.sha256).digest()
        cand = int.from_bytes(v, "big")
        if 1 <= cand < N: return cand
        k = hmac.new(k, v + b"\x00", hashlib.sha256).digest(); v = hmac.new(k, v, hashlib.sha256).digest()


def sign(priv: int, h: bytes):
    """Return (r, s, recid) for a 32-byte message hash; s is normalised to the lower half (EIP-2)."""
    z = int.from_bytes(h, "big")
    k = _rfc6979(priv, h)
    R = _mul(k, G)
    r = R[0] % N
    s = _inv(k, N) * (z + r * priv) % N
    recid = (R[1] & 1) | (2 if R[0] >= N else 0)
    if s > N // 2:
        s = N - s; recid ^= 1
    return r, s, recid


def verify(pub, h: bytes, r: int, s: int) -> bool:
    if not (1 <= r < N and 1 <= s < N): return False
    z = int.from_bytes(h, "big"); w = _inv(s, N)
    pt = _add(_mul(z * w % N, G), _mul(r * w % N, pub))
    return pt is not None and pt[0] % N == r


def recover(h: bytes, r: int, s: int, recid: int):
    x = r + (N if recid & 2 else 0)
    y2 = (pow(x, 3, P) + 7) % P
    y = pow(y2, (P + 1) // 4, P)
    if (y * y) % P != y2: return None
    if (y & 1) != (recid & 1): y = P - y
    R = (x, y); z = int.from_bytes(h, "big"); ri = _inv(r, N)
    return _mul(ri, _add(_mul(s, R), _mul((-z) % N, G)))
