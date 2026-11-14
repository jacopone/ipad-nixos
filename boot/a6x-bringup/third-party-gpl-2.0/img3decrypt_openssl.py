#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# parse_img3() below is adapted from Project Cascadia's img3decrypt.py
# (https://github.com/rzxvx/Project-Cascadia, commit 705fd31f014b226e663f1ab0009d138787fbfbd7,
# devices/a5/scripts/img3decrypt.py). GPL-2.0, per ./LICENSE in this directory
# -- NOT covered by this repo's top-level MIT LICENSE.
"""Decrypt an Apple IMG3 DATA payload, using `openssl` for the AES step instead of
pycryptodome (Cascadia's img3decrypt.py parsing logic, reimplemented without the
Crypto.Cipher dependency). Requires `openssl` on PATH."""
import struct
import subprocess
import sys


def parse_img3(data: bytes):
    magic, _total_len, _data_len = struct.unpack_from("<4sII", data, 0)
    if magic != b"3gmI":
        raise SystemExit(f"not an IMG3 file (got {magic!r})")
    off = 20
    while off < len(data):
        tag, tag_total_len, tag_data_len = struct.unpack_from("<4sII", data, off)
        if tag == b"ATAD":
            cipher_len = tag_total_len - 12
            if cipher_len % 16 != 0:
                raise SystemExit(f"ciphertext len {cipher_len} not block-aligned")
            return data[off + 12 : off + 12 + cipher_len], tag_data_len
        off += tag_total_len
    raise SystemExit("no DATA tag found")


def main():
    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} <in.img3> <out.bin> <iv-hex> <key-hex>", file=sys.stderr)
        return 2
    infile, outfile, iv_hex, key_hex = sys.argv[1:]
    raw = open(infile, "rb").read()
    ciphertext, plain_len = parse_img3(raw)
    proc = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-nopad", "-K", key_hex, "-iv", iv_hex],
        input=ciphertext,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(proc.stderr.decode(errors="replace"), file=sys.stderr)
        raise SystemExit("openssl decrypt failed")
    plain = proc.stdout[:plain_len]
    open(outfile, "wb").write(plain)
    print(f"wrote {len(plain)} bytes to {outfile} (ciphertext was {len(ciphertext)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
