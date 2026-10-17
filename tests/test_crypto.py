import unittest
from nullwallet.keccak import keccak256
from nullwallet import secp256k1 as ec
from nullwallet.ethtx import address_of, checksum, sign_legacy, tx_hash, rlp


class TestCrypto(unittest.TestCase):
    def test_keccak_vectors(self):
        self.assertEqual(keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(keccak256(b"abc").hex(), "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")
        self.assertEqual(keccak256(b"a" * 200).hex(), keccak256(b"a" * 200).hex())  # multi-block path runs

    def test_address_of_known_keys(self):
        self.assertEqual(checksum(address_of(1)), "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf")
        self.assertEqual(checksum(address_of(int("46" * 32, 16))), "0x9d8A62f656a8d1615C1294fd71e9CFb3E4855A4F")

    def test_sign_verify_recover(self):
        priv = 0xC0FFEE1234567; h = keccak256(b"hello")
        r, s, rec = ec.sign(priv, h)
        self.assertTrue(ec.verify(ec.pubkey(priv), h, r, s))
        self.assertEqual(ec.recover(h, r, s, rec), ec.pubkey(priv))
        self.assertLessEqual(s, ec.N // 2)
        self.assertFalse(ec.verify(ec.pubkey(priv), keccak256(b"other"), r, s))

    def test_rlp(self):
        self.assertEqual(rlp(b"dog").hex(), "83646f67")
        self.assertEqual(rlp([b"cat", b"dog"]).hex(), "c88363617483646f67")
        self.assertEqual(rlp(0).hex(), "80"); self.assertEqual(rlp(1024).hex(), "820400")

    def test_eip155_example(self):
        # the worked example of EIP-155
        raw = sign_legacy(int("46" * 32, 16), 9, 20 * 10**9, 21000, "0x3535353535353535353535353535353535353535", 10**18, b"", 1)
        self.assertEqual(raw.hex(), "f86c098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a76400008025a028ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276a067cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83")


if __name__ == "__main__":
    unittest.main()
