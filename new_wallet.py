"""Create a brand-new throwaway Ethereum wallet on YOUR computer (no MetaMask, no website, no account).
Prints the address (where you send a little ETH on the Base network) and saves the private key to throwaway_wallet.key
(this file name is already in .gitignore, so it cannot be committed by mistake). Never share the key with anyone."""
import os, sys, secrets
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import ethtx
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141   # secp256k1 group order
OUT = "throwaway_wallet.key"
if os.path.exists(OUT):
    key = open(OUT).read().strip(); print("Using the wallet already saved in", OUT)
else:
    k = 0
    while not (1 <= k < N): k = int.from_bytes(secrets.token_bytes(32), "big")
    key = f"{k:064x}"; open(OUT, "w").write(key + "\n"); print("Created a new wallet and saved the key to", OUT)
addr = ethtx.checksum(ethtx.address_of(int(key, 16)))
print("\nADDRESS (send ETH here, on the BASE network):", addr)
print("Check it later at: https://basescan.org/address/" + addr)
print("\nKEEP", OUT, "until you have finished the on-chain step. Do not email it, upload it or commit it.")
