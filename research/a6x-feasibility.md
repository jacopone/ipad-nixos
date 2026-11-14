## iPad 4 (A6X, S5L8955X, p102ap): roadmap and feasibility

Scope: a 32-bit Swift-core port, separate from the A8X chain this repo targets. This section uses only research findings, most of them read through a summariser. Nothing was run on an iPad 4, and no one is known to have booted Linux on one. The repo's own `CLAUDE.md` says "don't generalize across all iPads". An A6X port is therefore a second target with its own cost, not an extension of the A8X work.

### Verdict

- **Conditional go for a minimal, tethered result, as a reasoned starting point and not working A6X boot code.** A framebuffer console, a USB shell, and possibly SMP, touch and Wi-Fi are plausible. No A6X boot code exists in any source reviewed.
  - a6-handheld-linux targets the iPhone 5 (S5L8950X, A6, not A6X). Its own `BUILDING.md` says the scripts were never rerun from a fresh checkout, and its desktop result rests on the author's own `docs/test-results.md`, not on any reproduction.
  - Project Cascadia has a draft p102ap device tree and a parser that recognises `s5l8955x`. It has no A6X loader or boot code, and its loader is A5-specific.
  - checkm8_bootkit lists an A6X config entry (cpid `0x8955`). Its A6X offsets are unverified on real hardware, and a6-handheld demonstrates the tool only on A6.
  - That the A6X shares the "same Swift core" or a "same SoC family" boot environment with the A6 is the researcher's own inference. It is not a verified fact.
- **The boot is tethered and RAM-only.** Every boot needs a host running checkm8. A power cycle returns the device to iOS. Nothing persists on the device (see Storage below).
- **No-go on GPU.** See section 5.
- **Nothing has been proven on A6X hardware.** All A6X pieces are reasoned from sibling devices.

### Blockers and risks to resolve first

- **Open blocker: iOS version and firmware keys.** The firmware version to use is unresolved (a6-handheld: "likely 8.4.1 or 10.3.x"). The version changes the Mach-O layout, the keys and the load addresses. The research did not establish where iPad 4 decryption keys come from, and a6-handheld has no extraction guide for its Apple inputs. No image can be built until this is settled.
- **Hazard: battery discharge while tethered.** a6-handheld reports a phone discharging one night after losing the host, and that "the charger code cannot stop charging if the kernel hangs". On a large iPad battery this is a safety concern. Do not leave a tethered iPad unattended on an unproven kernel. Treat charging control as a risk to resolve before any long unattended run.
- **Unverified A6X exploit path.** That checkm8 runs from a PC host on A6X comes from general knowledge and the bootkit config entry. No A6X hardware evidence exists.
- **Variant ambiguity.** The Cascadia DTS identifies as iPad3,5 (a cellular iPad 4 variant) with a stale iPad2,5 header. The iPad 4 has three model numbers, and the research does not say which ones p102ap covers.

### 1. Smallest useful first milestone

**M0 (gate, no Linux): a pwned DFU on the iPad 4 that accepts a patched iBSS.**
- Run checkm8 (gaster or ipwndfu) on a PC host. The serial string must contain `PWND:[checkm8]`.
- Then run `checkm8_bootkit boot <iBSS>`. The A6X config entry is `loadaddr 0x10000000`, `loadsize 0x60000`. `0x10000000` is where bootkit loads the iBSS, not a DRAM base.
- bootkit constraints: the raw unpacked image must start with `0xEA00000E` and fit in `loadsize` (384 KiB) minus the payload. The tool does no signature patching and does not extract from an IPSW. Patched, decrypted iBSS and iBEC are mandatory inputs, and the 384 KiB limit applies to them.
- Pass condition, carried over from the iPhone 5 (N42) a6-handheld flow and unverified for A6X: the device reports DFU with IBFL `0x1b`, then Recovery after iBEC upload.
- This is a cheap yes/no on the exploit and loader chain, but it cannot start until the firmware-key blocker above is resolved.

**M1 (first real milestone): a coloured-screen handoff stub.**
- Keep the stub trivial and Linux-free. It paints iBoot's live framebuffer with a stage colour, as a6-handheld's `linux-handoff.S` does (red, then green, and so on).
- Why this first: both reference projects used the framebuffer as their first progress signal. It needs no UART, no kernel and no device tree.
- It would exercise the whole chain: pwn, patched iBSS/iBEC, DeviceTree img3, kernelcache wrapper, handoff.
- It also forces A6X-specific rework:
  - re-derive the Mach-O layout, the one-instruction entry patch and the cave address from the iPad 4 kernelcache (in a6-handheld the payload sits at Mach-O vm `0x80100000` and the handoff cave at `0x80cbb38c`; other offsets apply under feature flags, so this is approximate)
  - the img3 template and key/IV
  - the framebuffer base from `boot_args` (a6-handheld hardcodes `0xbf7aa000` and 640x1136; the iPad 4 panel is 2048x1536)
- Candidate boot route, as a starting point only: a6-handheld's (checkm8_bootkit, then `irecovery` for iBEC, DeviceTree and kernelcache img3, then `bootx`). Cascadia's route is A5-specific for these reasons:
  - it needs a Pi Pico for the A5 exploit
  - its loader assumes a Cortex-A9 plus PL310
  - every offset is tied to iBoot-2261 P105
  - its loader also disables the watchdog (`0x3F103020`) before the jump. a6-handheld's DTS lists a watchdog at `0x0f103020`, but its handoff stub does not mention disabling it. Whether A6X needs this is open.
- Not pursued: PC-less entry (A5 Pi Pico/kDFU paths, Cascadia's unfinished NAND "upgrade" patch). A kDFU/tfp0 route would need an A6X-specific jailbreak.
- Caveat: a6-handheld's scripts, including `scripts/build-a6-zimage.sh` (unread), were not run from a fresh checkout. Expect friction.

### 2. Ordered milestones after M1

| # | Milestone | Evidence it is reachable | Main risk |
|---|---|---|---|
| M2 | Kernel boots to earlycon or simpledrm text on iBoot's framebuffer; AIC and timer up, single core | a6-handheld AIC (`apple,s5l8950-aic`) and timer drivers are marked "reuse with checks". Cascadia's issue #6 gives A6X `aic,1` at physical `0x3f200000` and says it matches Cascadia's AIC1 driver | These may be different drivers: a6-handheld's register map (EVENT `0x2004`, TARGET_CPU `0x3000`, and so on) must be compared with the iPad 4 ADT. CNTFRQ (SMP bridge insists on 24 MHz) and UART base (`0x32600000` is the iPhone 5 value; Cascadia uses a different UART) are unverified on A6X. Draft DTS has a 512 MiB RAM placeholder (marked patched at boot) and zeroed initrd addresses, while the a6-handheld finding says 1 GiB. The mainline kernel base is undecided (Cascadia pins v6.12; a6-handheld's is unstated) |
| M3 | initramfs shell reachable over USB gadget (dwc2) | a6-handheld dwc2 patches likely target the same IP block (unverified on A6X) | PHY magic values (`0x749`, `0x2ff3`, `0x200`) are unexplained. Large USB transfers stall upstream (cause unknown) |
| M4 | Second Swift core (SMP) | a6-handheld has both cores, with local-TLBI and cache workarounds | Worked only after trial and error (many `a6-cpu1-*` probes). PMGR offsets (`0x214`/`0x220` for CPU1 release) and reset-page aliasing are unverified on A6X. Optional: single-core is a usable stop |
| M5 | Touch | This repo's Z2 protocol research (frame format, commands, finger struct, firmware/cal load) is SoC-independent if the chip is Z2 | Chip family is unconfirmed. `touch-re.md` asserts BCM5976 for the iPad 3 as fact while `touch-deep-dive.md` says it is unconfirmed, and the two files disagree on 0xD9 report offsets. "Z2F13" is an iOS driver name, not a part number. Cascadia's issue says `spi3` for the iPad 4 and a6-handheld's iPhone 5 touch uses SPI1 (controller chip unidentified); the A8X SPI controller is not reusable. Calibration and firmware are per-device and IPSW-derived |
| M6 | Wi-Fi (Broadcom over HSIC; chip unconfirmed) | Issue #6 says BCM4334 "matching the A5 setup". a6-handheld ran BCM4334 on iPhone 5 with stock `brcmfmac` plus an HSIC framing patch | Sources conflict: only the Cascadia author's unverified claim names BCM4334 for the iPad 4, and a6-handheld says the iPad 4 uses a different Broadcom part and board. HSIC topology may differ. Link stalls exist upstream (cause unknown). Firmware and NVRAM come from the iPad's IPSW |
| M7 | Software-rendered desktop (simpledrm + Pixman, as a6-handheld did with labwc) | Claimed for iPhone 5 at 640x1136 in the author's own `docs/test-results.md`; not reproduced elsewhere | Performance at 2048x1536 on 1 GiB RAM with CPU rendering is untested. Treat as unknown. Initramfs size is bounded by the kernel payload limits noted in M1 |
| M8 | Storage / persistence (rootfs beyond RAM) | None found. The driver-gap doc rates Storage High effort, as an inference from absence of evidence plus the repo's own driver-gap analysis (A8X's APPLE_ASP and A7/A8-era ANS1 do not apply to A6X) | Until this is done, the system lives in a RAM initramfs (or USB/NFS rootfs) and every boot needs the host. NAND/LwVM layout would need re-derivation for A6X. Explicitly deprioritised relative to M2-M7, not dropped: it decides whether the device is usable without a tether |

Open and not yet covered by any milestone: whether neither reference has a DART driver (the A6X ADT lists dart-rt and dart-nrt IOMMUs for the GPU) or whether non-GPU DMA needs one.

Deprioritised, with no evidence they are worth the effort: audio (codec and wiring are board-specific, sequences replayed from stock firmware), Bluetooth (a6-handheld: not implemented; Cascadia's uart3 at `0x32300000` must be checked against the chosen console UART), backlight (a6-handheld has no driver, fixed brightness), battery fuel gauge (a6-handheld: not working), cameras, sensors, suspend.

### 3. Relative effort

The research did not find usable start or end dates for either reference project, so no duration can be stated.
- Cascadia: dated artifacts run from 2026-10 to 2026-11-08, but these are issue, PR and newest-commit dates. No start date was found.
- a6-handheld-linux: one squashed commit, with `docs/test-results.md` dated 2026-10-15. The development timeline is invisible.

Qualitative comparison only:
- **Boot chain and CPU/SMP/IRQ/timer:** probably closer to a6-handheld, on the inference that the S5L895x boot environment and Swift core are shared with the A6 (unverified). Its cache, TLB and SMP findings might transfer. Cascadia's Cortex-A9/PL310 loader assumptions do not apply (no PL310 on A6X, per issue #6).
- **Peripherals (touch, Wi-Fi, display):** closer to Cascadia's iPad experience, and the iPad 4 DTS and the parser generalisation (PR #7) already exist. The peripheral work still has to be redone, because the DTS summary shows no nodes for touch, GPU, Wi-Fi or DART.
- **Risk compared with the A5 port:** both references got there with each stage hand-derived from iOS captures and ADT data. Both needed several debugging iterations on SMP and USB. Assume the A6X is not materially cheaper on the parts that were hard for them (SMP, USB, power), and cheaper only where a driver or technique can be copied (AIC, timer, dwc2, brcmfmac framing, handoff idea).
- The driver-gap effort labels (Medium for CPU/AIC and USB) understate the trial-and-error history on SMP and USB. Its Display "Low" applies only to the iBoot framebuffer, not to software rendering at 2048x1536 (M7).

### 4. NixOS-specific work: reuse vs net-new

**Reuse from the existing A8X setup:**
- flake and devenv structure
- `makeInitrdNG`, the static busybox, dropbear and kmod pattern, and the `#!/bin/ash` init script (architecture-neutral recipes)
- zstd/lzma/gzip initramfs options
- the `buildLinux` skeleton
- the pinned gaster package (host-side exploit tooling)
- this repo's touch protocol research (see M5)

**Net-new:**
- **32-bit cross-compilation:** `crossSystem` becomes `armv7l-unknown-linux-gnueabihf` (`lib.systems.examples.armv7l-hf-multiplatform`). A musl variant (`armv7l-unknown-linux-musleabihf`) is inferred by analogy to the armv6l muslpi example, not copied from an armv7l musl example in nixpkgs. It was not evaluated.
- **No binary cache for armv7l:** the NixOS wiki says no cache is published for ARMv6/ARMv7. Hydra cross-builds `armv7l-hf` glibc for a subset only, and the musl cross toolchain is not a Hydra job. Expect long first local builds; check with `nix build --dry-run`.
- **Kernel config rewrite:**
  - Pass `defconfig = "multi_v7_defconfig"` explicitly (nixpkgs defaults to plain `defconfig` for armv7).
  - Drop `ARM64_16K_PAGES` and the arm64-oriented Apple AIC and SPI options.
  - Use `ARCH_MULTI_V7`, `CPU_V7`, VFP/NEON and `ARM_APPENDED_DTB`.
  - `ignoreConfigErrors = true` in the current kernel derivation would hide mistakes, so remove it for this target.
  - The mainline base version is undecided (see M2).
- **Image format:** `zImage` plus an appended DTB (`cat zImage dtb`). The kernel patches come from a6-handheld and Cascadia, not nixpkgs. Total size (zImage plus embedded initramfs) is bounded by the Mach-O payload and cave layout noted in M1, so a Nix-built initramfs must stay small. The bound is approximate.
- **FPU:** the nixpkgs default `vfpv3-d16` works but leaves NEON/VFPv4 unused. An override is untested.
- **musl on armv7l:** busybox, dropbear and kmod are untested here. Historical time64/stat64 quirks are possible.
- **Boot packaging:** an IMG3 kernelcache wrapper (xpwntool template, one-instruction entry patch, handoff stub in a Mach-O cave) is the approach taken by the a6-handheld and Cascadia flows, which use iBSS/iBEC. The A8X chain in this repo uses pongoOS; the findings show only that the A5 and A6 chains reviewed use iBSS/iBEC. Cascadia's loader sits in a `pongo/` directory and its README mentions a pongo module, so whether pongoOS plays any role on A6X is not settled by the research and needs a precise citation before being stated as fact.
- **Firmware extraction:** iBSS, iBEC, DeviceTree, kernelcache and the later peripheral firmware blobs come from the user's own iPad 4 IPSW. Nothing is shipped. The IPSW version and key source are an open blocker (see above).

### 5. Not worth pursuing: GPU

The research supports an explicit no-go:
- The only claim that the SGX554MP4 can reuse SGX543 work is the Cascadia maintainer's comment in issue #6. No code backs it.
- Cascadia's A5 GPU stack (kernel DRM driver, Mesa Gallium driver with its own NIR-to-USSE compiler, firmware from the IPSW) was built by differential reverse engineering of iOS 8.4.1 on A5. Its own README still lists limits on A5: one render in flight, polled completion (the interrupt was "never seen to fire"), no mipmaps.
- A6X would need new firmware, new traces, a retargeted kext emulation, validation against 8-wide ALUs (per AnandTech, via a search snippet only), and a 4-core path whose behaviour is undocumented.
- Nothing open exists for SGX Series 5 beyond Cascadia. a6-handheld lists the GPU as not supported with no reason given.
- Payoff: a software-rendered desktop (M7) is claimed to work on iPhone 5, and is untested at iPad 4 resolution. GPU is the single largest cost for the smallest gain on this target.

Recommendation: stop at M7 (and decide on M8 separately), and revisit the GPU only if Cascadia publishes A6X GPU work. Backlight, battery gauge and audio are also unproven and low payoff.

### Open items to verify before committing (all read through a summariser)
- Firmware source: which iOS version (8.4.1 vs 10.3.x) the iPad 4 inputs come from, and where the keys come from.
- A6X DTS contents (the summary showed no Z2, GPU, Wi-Fi or DART nodes, and a stale iPad2,5 header). Clone Cascadia and run `grep -ril "8955\|p102"` to close the tree-truncation gap. Also confirm which iPad 4 model numbers p102ap covers.
- The A6X addresses in issue #6 (AIC, `spi3`, UART3, GPU) are the author's claims, not independently verified.
- a6-handheld's SMP, PMGR and USB PHY findings and `scripts/build-a6-zimage.sh` (unread); the 1 GiB vs 512 MiB RAM discrepancy; the CNTFRQ 24 MHz assumption.
- Whether the A6X needs the watchdog disabled before handoff.
- Whether the iPad 4 digitizer is a Z2 device at all, and which Broadcom Wi-Fi part it uses.
- Whether any DART driver is needed for non-GPU DMA.
- Charging control behaviour under a hung kernel on the iPad 4 battery.
