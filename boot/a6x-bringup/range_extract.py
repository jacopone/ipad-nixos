#!/usr/bin/env python3
"""Extract specific entries from a remote ZIP (IPSW) without downloading the whole file,
using HTTP Range requests. Relies only on urllib (stdlib) + zipfile (stdlib)."""
import io
import sys
import urllib.request
import zipfile

URL = "https://secure-appldnld.apple.com/ios8.4.1/031-31187-20150812-751A8A7E-3C8F-11E5-B300-B71A3A53DB92/iPad3,6_8.4.1_12H321_Restore.ipsw"
SIZE = 1845205928
TARGETS = [
    "Firmware/dfu/iBSS.p103.RELEASE.dfu",
    "Firmware/dfu/iBEC.p103.RELEASE.dfu",
    "Firmware/all_flash/all_flash.p103ap.production/DeviceTree.p103ap.img3",
]
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url, size, chunk=512 * 1024):
        self.url = url
        self.size = size
        self.chunk = chunk
        self.pos = 0
        self._cache_start = None
        self._cache_data = b""
        self.requests_made = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.size + offset
        return self.pos

    def tell(self):
        return self.pos

    def _ensure_cached(self, start, length):
        end_needed = start + length
        if (
            self._cache_start is not None
            and start >= self._cache_start
            and end_needed <= self._cache_start + len(self._cache_data)
        ):
            return
        fetch_start = max(0, start - 4096)
        fetch_len = max(self.chunk, length + 8192)
        fetch_end = min(self.size - 1, fetch_start + fetch_len - 1)
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={fetch_start}-{fetch_end}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        self.requests_made += 1
        self._cache_start = fetch_start
        self._cache_data = data

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if self.pos >= self.size:
            return b""
        n = min(n, self.size - self.pos)
        self._ensure_cached(self.pos, n)
        off = self.pos - self._cache_start
        out = self._cache_data[off : off + n]
        self.pos += len(out)
        return out

    def readinto(self, b):
        data = self.read(len(b))
        n = len(data)
        b[: n] = data
        return n


f = HTTPRangeFile(URL, SIZE)
z = zipfile.ZipFile(f)
names = z.namelist()
print(f"zip opened OK via range requests, {len(names)} entries, {f.requests_made} HTTP requests so far")

import os
os.makedirs(OUT_DIR, exist_ok=True)
for t in TARGETS:
    if t not in names:
        print(f"MISSING in archive: {t}")
        continue
    data = z.read(t)
    out_path = os.path.join(OUT_DIR, os.path.basename(t))
    with open(out_path, "wb") as fh:
        fh.write(data)
    print(f"extracted {t} -> {out_path} ({len(data)} bytes)")

print(f"total HTTP range requests used: {f.requests_made}")
