#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# parse_img3() below is adapted from Project Cascadia's img3decrypt.py
# (https://github.com/rzxvx/Project-Cascadia, commit 705fd31f014b226e663f1ab0009d138787fbfbd7,
# devices/a5/scripts/img3decrypt.py) with the AES backend swapped for an
# `openssl` subprocess call. GPL-2.0, per ./LICENSE in this directory --
# NOT covered by this repo's top-level MIT LICENSE.
import json
import os
import struct
import subprocess
import sys

WORK = sys.argv[1]
KEYS_JSON = sys.argv[2]

FILES = {
    "iBSS": "iBSS.p103.RELEASE.dfu",
    "iBEC": "iBEC.p103.RELEASE.dfu",
    "DeviceTree": "DeviceTree.p103ap.img3",
}


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


def decrypt(ciphertext: bytes, plain_len: int, iv_hex: str, key_hex: str) -> bytes:
    proc = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-nopad", "-K", key_hex, "-iv", iv_hex],
        input=ciphertext,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.decode(errors="replace"))
    return proc.stdout[:plain_len]


keys = json.load(open(KEYS_JSON))["keys"]
by_image = {}
for e in keys:
    if e.get("image") in FILES and len(e.get("key", "")) == 64 and e.get("iv") and e["image"] not in by_image:
        by_image[e["image"]] = e

for image, fname in FILES.items():
    if image not in by_image:
        print(f"NO KEY for {image}")
        continue
    e = by_image[image]
    raw = open(os.path.join(WORK, fname), "rb").read()
    ciphertext, plain_len = parse_img3(raw)
    plain = decrypt(ciphertext, plain_len, e["iv"], e["key"])
    out = os.path.join(WORK, fname + ".decrypted")
    open(out, "wb").write(plain)
    print(f"{image}: {fname} -> {out}  ({len(plain)} bytes plaintext, {len(ciphertext)} bytes ciphertext)")
