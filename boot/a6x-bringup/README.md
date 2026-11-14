# A6X hardware bring-up tooling (iPad 4 / P103AP)

Secondary track (see `research/a6x-*.md` and `CLAUDE.md`): getting a personal
iPad 4 (model A1460, board P103AP, Apple A6X / S5L8955X, CPID `0x8955`,
shipped iOS 10.3.4) to boot something other than stock iOS, via checkm8.
This is **not** the repo's primary target (iPad Air 2 / A8X) — A6X has no
pongoOS support (pongoOS only targets A7-A11) and uses the older
checkm8 → patched iBSS/iBEC → kernel chain instead.

This directory holds the tooling built to get from "checkm8-exploitable
device" to "patched bootloader ready to try booting", plus the real
hardware findings so far. Nothing here embeds firmware, decryption keys, or
other Apple-copyrighted binary data — see "What is intentionally not here"
below.

**Licensing note**: this directory mixes this repo's MIT license with
GPL-2.0 third-party code. `third-party-gpl-2.0/` contains code vendored
from, or directly adapted from, [Project Cascadia](https://github.com/rzxvx/Project-Cascadia)
(GPL-2.0) — see that subdirectory's own `LICENSE` and per-file headers.
Everything else in this directory is original and MIT-licensed like the
rest of the repo. `libirecovery-skip-set-interface.patch` is a patch
against upstream `libimobiledevice/libirecovery`, which is LGPL-2.1 — the
patch itself is not a redistribution of that project's source.

## Pipeline

1. **Source firmware decryption keys.** `theiphonewiki.com` is down (HTTP
   504, persistent) and the Wayback Machine mirror is not fetchable from
   this tooling's environment. Use `api.ipsw.me` instead:
   `https://api.ipsw.me/v4/keys/ipsw/<device-id>/<build>` (e.g.
   `iPad3,6`/`12H321`) — same key/IV data, different host.
2. **Extract firmware components from the IPSW without downloading 1.76GB.**
   `range_extract.py <out_dir>` opens Apple's real signed IPSW URL (the URL
   is public and hardcoded in the script) via HTTP Range requests, wrapped
   in a `zipfile.ZipFile`-compatible `io.RawIOBase`, and pulls only
   `iBSS.p103.RELEASE.dfu`, `iBEC.p103.RELEASE.dfu`, and
   `DeviceTree.p103ap.img3`. (A plain full-file `curl` silently truncated at
   63MB/1.76GB for us — exit 0, no `-f` — which is what motivated this.)
3. **Decrypt the IMG3 containers.** `decrypt_all.py <work_dir> <keys.json>`
   (batch, keyed off the `api.ipsw.me` JSON) or `img3decrypt_openssl.py
   <in.img3> <out.bin> <iv-hex> <key-hex>` (single file, explicit key/iv).
   Both reimplement IMG3 parsing (magic `3gmI`, `ATAD` tag, AES-CBC
   ciphertext truncated to `tag_data_len` *after* decrypt) and shell out to
   `openssl enc -d -aes-256-cbc -nopad` instead of requiring pycryptodome.
4. **Patch iBSS/iBEC.** Use the real `iBoot32Patcher` (NyanSatan's fork,
   originally iH8sn0w/tihmstar, GPL-3.0 — not vendored here, clone it
   yourself) against the two `.decrypted` files:
   `iBoot32Patcher iBSS.p103.RELEASE.dfu.decrypted iBSS.p103.patched -r -b
   "cs_enforcement_disable=1 debug=0x14"` (same for iBEC). `-r` is the RSA/
   signature-check patch ("all loaders have it" per upstream); boot-args are
   only applied if the image `has_kernel_load`. On modern clang this needs
   `-Wno-error=int-conversion` to build (`patchers.c:320` triggers the
   stricter default).
5. **Generate a Linux device tree from Apple's ADT.** `third-party-gpl-2.0/adt_to_dts.py`
   + `dtparse.py` are Project Cascadia's ADT→DTS converter
   (github.com/rzxvx/Project-Cascadia, commit `705fd31f`,
   `devices/a5/src/{adt_to_dts.py,dtparse.py}`, GPL-2.0) — vendored here
   because the public copy ships `adt_to_dts.py` without its `dtparse`
   sibling module, which breaks the import otherwise. Usage:
   `python3 third-party-gpl-2.0/adt_to_dts.py DeviceTree.p103ap.img3.decrypted -o p103ap.dts`
   (run with both files in the same directory — `-I` isolated mode breaks
   the same-directory import). `p103ap.dts` in *this* directory (not the
   GPL subdirectory — it's generated data, not code, so it stays MIT like
   the rest of the repo) is the real
   output for this device: `apple,s5l8955x` / `apple,ipad3,6`, dual
   `apple,swift` CPUs, SoC base `0x30000000` — `memory@0` and the
   framebuffer/initrd fields are placeholders patched at boot, not from the
   static ADT.
6. **Boot it.** `checkm8_bootkit` (NyanSatan, originally Mac/IOKit-only via
   a `lilirecovery` fork) ported to run natively on Linux:
   `checkm8-bootkit-linux-shim/lilirecovery.h` redirects its
   `#include <lilirecovery.h>` to the real, portable
   `libimobiledevice/libirecovery` (can't be done with a `-D` macro —
   preprocessor doesn't substitute inside `#include <>` filenames, so this
   needs to be a real file first on the include path); `batch_stub.c` stubs
   out the Objective-C `batch.m` dependency (`batch_init`/etc.) that
   `main.c` references unconditionally even though only the `boot` verb is
   used. Link against `-lirecovery-1.0` (that's the nixpkgs library name,
   not `-lirecovery`). Its `src/libbootkit/config.h` already ships the A6X
   entry (cpid `0x8955`, `s5l8955x`, load addr `0x10000000`) and
   `payload.h` already has the precompiled ARM shellcode — nothing to add
   there. Run as `checkm8_bootkit boot iBSS.p103.patched` after `gaster pwn`.

## Hardware fixes found so far

**Fixed** — `libirecovery-skip-set-interface.patch` (against upstream
`libimobiledevice/libirecovery` commit `3301fe7d834a485b368cd7edf20f7535d6d598b4`,
file `src/libirecovery.c`, inside `irecv_open_with_ecid()`): real
libirecovery unconditionally calls `irecv_usb_set_interface()`
(`libusb_claim_interface` + `set_interface_alt_setting`) on open.
`checkm8_bootkit` only ever does control transfers to ep0, which don't need
an interface claim on Linux, and this device's exploited bootROM USB stack
does not appear to answer that SET_INTERFACE request — it hung forever.
`gaster` (0x7ff/gaster), which never claims an interface and always works
against this device, is the evidence for the diagnosis. The patch wraps the
set-interface block in `if (0) { ... }`; every other libirecovery caller is
unaffected except `irecv_open_with_ecid()` itself, which now never claims an
interface (bulk-transfer callers would need it back).

**Not yet fixed** — second, different hang: after the patch above, `gaster
pwn` *itself* (not checkm8_bootkit — a tool that had worked all night) got
stuck before finishing its RESET stage. `strace -f -p <pid>` showed an
infinite retry loop: reopen the `/dev/bus/usb/...` node → `SETCONFIGURATION`
→ `SUBMITURB` → poll → `REAPURBNDELAY` returns `-1 EAGAIN` every time (no
response inside the ~11ms window) → discard → close → sleep 5ms → repeat.
The device enumerates at the kernel/USB level (`lsusb` shows `05ac:1227`)
but answers no control transfers. This can't be the same bug (gaster never
claims an interface), so it's a different, unconfirmed issue — current
working theory is device-USB-stack fragility after repeated DFU cycling
rather than a tooling bug. **Next diagnostic step**: after a fresh
power-off → DFU entry, run bare `gaster pwn` alone (no chaining) to see if
it recurs in isolation before re-chaining `checkm8_bootkit`.

## What is intentionally not here

No firmware binaries (encrypted or decrypted), no decryption keys, and no
patched bootloader binaries are committed — this is a public repo and those
are Apple's copyrighted firmware/key material. Re-derive them locally with
the pipeline above; they take minutes, not hours, once the tooling exists.

## Credits

- [0x7ff/gaster](https://github.com/0x7ff/gaster)
- [NyanSatan/checkm8_bootkit](https://github.com/NyanSatan/checkm8_bootkit)
- [NyanSatan/iBoot32Patcher](https://github.com/NyanSatan/iBoot32Patcher)
  (originally iH8sn0w/tihmstar)
- [libimobiledevice/libirecovery](https://github.com/libimobiledevice/libirecovery)
  (LGPL-2.1)
- [rzxvx/Project-Cascadia](https://github.com/rzxvx/Project-Cascadia)
  (GPL-2.0 — `adt_to_dts.py`/`dtparse.py` vendored verbatim in
  `third-party-gpl-2.0/`; `decrypt_all.py`/`img3decrypt_openssl.py`'s
  `parse_img3()` adapted from its `img3decrypt.py`)
