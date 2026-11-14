# Driver Gap Analysis: iPad 4 (A6X, S5L8955X)

Per-subsystem analysis of iPad 4 (board p102ap, iPad3,5 in the Cascadia DTS) hardware and Linux driver status.
Research conducted 2026-11-14. Companion to research/driver-gap.md (iPad Air 2, A8X).

Scope and evidence quality:
- Almost all A6X hardware figures come from one source: Project Cascadia issue #6 (author's own
  hardware map, closed 2026-10-10) and PR #7 (`p102ap.dts`, 483 lines). Neither is independently
  verified, and the DTS was read only as a summary.
- No source in this research shows Linux booting on an A6X. Nothing was tested on an iPad 4.
- The only Linux-on-Apple-32-bit work with working peripherals is Cascadia on A5 (iPad mini 1,
  p105ap) and a6-handheld-linux on A6 (iPhone 5, N42AP, S5L8950X). a6-handheld-linux targets the A6, not
  the A6X. Transfer to A6X is inference from SoC-family similarity (for example "same Swift core" is
  inferred, never verified), marked as such below.
- The effort ratings in this document are judgements, not measurements. Where a rating rests on absence of
  evidence or on this repo's own research/driver-gap.md rather than on the raw external findings, the section
  says so.
- Findings were fetched through summarizing tools. Re-verify any address against the raw files
  before relying on it.
- Variants: the Cascadia DTS identifies as iPad3,5, a cellular iPad 4 variant. The iPad 4 shipped under three
  model numbers, and no finding says which variants p102ap covers or whether Wi-Fi-only variants share the
  board. Variant handling is unresolved.

## Summary Matrix

| Subsystem | Chip | Linux Driver | Status on A6X | Effort |
|-----------|------|-------------|---------------|--------|
| CPU / IRQ | Dual Apple Swift (ARMv7s), AIC v1 at 0x3f200000 | `irq-apple-a6-aic.c`, `timer-apple-a6.c` (a6-handheld-linux) | Reusable on A6, unverified on A6X | Medium |
| Touch | Apple Z2 family on spi3 per Cascadia issue #6 only (chip part unconfirmed; A6X SPI controller unknown) | apple_z2 (adapt), Cascadia mtcal tooling | Protocol documented, no A6X driver | Medium |
| Display | CLCD + eDP at 0x39500000, 2048x1536 | simplefb / simpledrm via iBoot framebuffer | Concept proven on A6, not on A6X. Rating covers the iBoot framebuffer only | Low (framebuffer only) |
| GPU | PowerVR SGX554MP4 | None (Cascadia `apple-sgx` + Mesa `sgx` is SGX543MP2 only) | None | Very High |
| Wi-Fi | BCM4334 over HSIC per Cascadia issue #6 only. OPEN CONFLICT with a6-handheld-linux ("different Broadcom part") | brcmfmac | Working on A5 and A6, unverified on A6X | Medium (rises if chip differs) |
| Bluetooth | uart3 at 0x32300000 | btbcm / hci_bcm | Working on A5 only | Medium |
| Storage / NAND | Pre-ANS1 Apple NAND, no source identifies the A6X controller | None identified | None | High (inference from absence of evidence) |
| Audio | Codec not identified for iPad 4 | None for iPad 4 | None | High |
| USB | EHCI/OHCI + OTG PHY, DWC2 gadget on A6 | dwc2 (patched), `phy-apple-s5l-usb.c` | Working on A5/A6, unverified on A6X | Medium |

Note on the labels: Medium for CPU/AIC and USB does not mean easy. In both reference projects SMP bring-up and USB
were trial and error (see sections 1 and 9). The Medium labels differentiate poorly between these risky items
and the better-understood ones such as Wi-Fi firmware extraction. Treat CPU/AIC SMP and USB as the higher-risk
Mediums.

---

## 1. CPU and Interrupt Controller

### Hardware

- **CPU**: dual Apple Swift cores (ARMv7s). The Cascadia p102ap DTS lists two Swift cores with
  the second disabled.
- **L2 cache**: none external. Issue #6 states A6X has no PL310, unlike A5.
- **Interrupt controller**: `aic,1` at local 0x0f200000, physical 0x3f200000, size 0x10000
  (issue #6, which says it matches Cascadia's AIC1 driver).
- **Memory**: the DTS has a 512 MiB placeholder at `memory@0`, marked to be patched at boot. The
  iPad 4 has 1 GiB (the 1 GiB figure comes from the a6-handheld-linux finding, which states it for its own
  board). The 1 GiB versus 512 MiB difference is a build discrepancy to resolve from the iPad 4's ADT, not a
  DRAM base. (checkm8_bootkit's 0x10000000 is the iBSS load address, not a DRAM base.)
- **Watchdog**: Cascadia's loader explicitly disables the watchdog (0x3F103020) before the jump.
  a6-handheld-linux's DTS lists a watchdog at 0x0f103020 (the same address, local view), but its handoff stub
  does not mention disabling it. Whether A6X needs the watchdog disabled is an open question.

### Linux Driver Status

**Status: reusable code exists for the A6 (S5L8950X); nothing has run on A6X.**

From a6-handheld-linux (iPhone 5, boots to a userland with both cores running):
- `kernel/platform/irq-apple-a6-aic.c` (`apple,s5l8950-aic`): IRQ count is read at runtime from the
  `INFO` register (offset 0x0004), so it is not hardcoded. Register map: `EVENT` 0x2004,
  `TARGET_CPU` 0x3000, `MASK_SET`/`MASK_CLR` 0x4100/0x4180. All IRQs route to CPU0, IPIs are
  multiplexed over one hardware IPI. The finding rates this the strongest candidate for direct
  reuse, conditional on A6X using the same AIC revision.
- Open question: the a6-handheld-linux AIC and Cascadia's `aic,1` at 0x3f200000 may be different drivers
  with different register maps. The a6-handheld-linux register map above must be compared against the
  iPad 4's ADT before AIC reuse is assumed straightforward.
- `kernel/platform/timer-apple-a6.c`: uses the ARMv7 generic-timer CP15 interface, not an S5L
  timer block. The compatible is `apple,s5l8950-timer`, so A6X needs a new compatible or a match
  on `apple,s5l8955`. The SMP bridge requires CNTFRQ of exactly 24 MHz (an assumption); A6X's value is
  unchecked.
- `kernel/a6-minimal.config` and the DTS `cpus` node use `compatible = "apple,swift", "arm,cortex-a9"`
  with `CONFIG_CPU_V7` / `ARCH_MULTI_V7`.
- SMP (`kernel/platform/a6-smp.c`) is a one-shot "bridge": PMGR at 0x3f101000, writes of 2 to
  offsets 0x214 and 0x220 to release CPU1, and an `LDR PC` table in the reset page aliased to RAM
  at physical 0. The many `a6-cpu1-*` cache and TLBI probes, plus the `a6-smp-local-tlbi` patch,
  show CPU1 bring-up was trial and error, and Linux needed local-only TLB invalidation on Swift.
  Whether A6X shares these PMGR offsets (0x214 and 0x220) is unverified.

From Cascadia:
- The loader (`devices/a5/pongo/linux_boot*.{c,S}`) assumes Cortex-A9 plus a PL310 at 0x3e000000
  (L2 clean/invalidate by way), reads CBAR with `mrc p15,4,c15,c0,0`, and parks cores by MPIDR.
  The A6X has Swift and no PL310, so the cache and L2 code needs rework (the "no PL310 on A6X"
  point is from issue #6; the "Swift is not A9" point is the finding's general knowledge).
- `devices/a5/src/adt_to_dts.py` already recognises `s5l8955x`. PR #7 generalised it: CPU compatible
  now comes from the ADT cpu node (expected `apple,swift`, fallback `arm,cortex-a9`), so A6X support
  is a generalisation of the A5 parser, not a separate path. The findings do not say whether PR #7 also
  removed the A5 hard-codes (the `apple,s5l8940x-<name>` prefix rewrite, `LINUX_COMPAT_MAP`, the
  `pl310@3e000000` label); if not, they mislabel A6X nodes.

### Estimated Effort

Medium (judgement). Justification: the AIC and timer drivers exist and are tested on a sibling SoC, and the A6X AIC
base is documented. The cost is that nothing is verified on A6X: the AIC revision and register map, timer
compatible and CNTFRQ, the PMGR and reset-page SMP release, the watchdog, and the loader's Cortex-A9 and PL310
assumptions all need re-derivation from the iPad 4's own ADT. SMP was trial and error in a6-handheld-linux, so the
SMP part is higher risk than the Medium label alone suggests. Single-core boot is a plausible first milestone
before SMP.

Sources:
- https://github.com/rzxvx/Project-Cascadia/issues/6
- https://github.com/rzxvx/Project-Cascadia (`devices/a5/pongo/linux_boot.c`, `devices/a5/src/adt_to_dts.py`)
- https://github.com/landrucode/a6-handheld-linux (`kernel/platform/irq-apple-a6-aic.c`, `timer-apple-a6.c`, `a6-smp.c`)

---

## 2. Touch

### Hardware

- **Controller family**: Apple Z2 on `spi3` (issue #6, the only source for this). The A5 iPad mini 1 uses
  `spi1`; the Cascadia `mtcal` tool was extended in PR #7 to try `arm-io/spi3/multi-touch`. For contrast,
  a6-handheld-linux's iPhone 5 touch uses SPI1 (0x32100000), and its touch controller chip is unidentified in
  the files read. The iPad 4 spi3 claim is therefore not corroborated by either reference project.
- **A6X SPI controller: unknown.** No finding describes the A6X's own SPI block. The A8X SPI controller
  work in this repo does not carry over to the A6X.
- **Chip part number**: unconfirmed. This repo's research never names the iPad 4 or A6X in a touch
  context. The iOS driver name AppleMultitouchSPIZ2F13 ("Z2F13") is a driver name, not a part number, and this
  repo never maps it to a chip. The Z2 protocol family spans different ICs (research/touch-deep-dive.md:248-251
  calls the iPhone 7 controller a different IC than the BCM5976 that still speaks Z2).
- The DTS summary showed no Z2 node, so the touch node still has to be written.

### Existing contradictions in this repo's own touch research

Two files in this repo disagree with each other, and neither contradiction is resolved here:
- **Chip identity for the iPad 3 (A5X)**: research/touch-re.md:533 asserts the BCM5976 as fact, while
  research/touch-deep-dive.md:268-270 says it is unconfirmed. The BCM5976 identification for the nearest
  32-bit evidence should be treated as unconfirmed.
- **0xD9 report offsets**: research/touch-deep-dive.md and research/touch-re.md give different offsets.
  Verify against hx-touchd before using either.

### Linux Driver Status

**Status: none on A6X. Protocol research from this repo's own Air 2 work may transfer, conditional on
the iPad 4 digitizer being a Z2 device, which only Cascadia issue #6 asserts.**

What may transfer from the A8X (Air 2) research in this repo. The Z2 protocol is independent of SoC
and SPI controller (research/touch-re.md:600-602):
- SPI frame format: 16-byte frames, 14 data bytes plus 2-byte checksum, 1000 us CS delays
  (research/touch-deep-dive.md:93-100; research/touch-re.md:337-342).
- Command set 0xE1-0xEE and 0xEB interrupt read (research/touch-deep-dive.md:101-114, 175;
  research/touch-re.md:344-354, 386-393).
- Report IDs 0x9D, 0xAF, 0xBF, 0xD9 (research/touch-deep-dive.md:116-130; research/touch-re.md:376-384).
  The two files disagree on the 0xD9 offsets (see above).
- Finger structure, about 32 bytes per finger, bcm5974 `tp_finger` layout
  (research/touch-deep-dive.md:157-217, 392-410; research/touch-re.md:227-247, 413-442).
- Firmware and calibration load model: container magic 0x5746325A, load commands 0/1/2,
  calibration via `apple,z2-cal-blob` up to 4096 bytes (research/touch-deep-dive.md:153-186, 412-431;
  research/touch-re.md:252-281).
- Control lines MT_SELECT, MT_RESET, MT_ATTN and PMU rail setup (research/touch-deep-dive.md:280-296;
  research/touch-re.md:505-520). These come from the iPad 3 (A5X, 32-bit) via lemonjesus, the closest
  32-bit evidence in the repo (research/touch-deep-dive.md:268-270; research/touch-re.md:492-535), subject to
  the chip-identity contradiction above.
- Driver plan: adapt apple_z2 and reuse Asahi `multitouch.py` for firmware extraction
  (research/touch-deep-dive.md:614-647; research/touch-re.md:913-958).

What does not transfer:
- The A8X SPI controller work (Samsung-derived, research/touch-deep-dive.md:595-601, 855-863) and the
  T7001/J82AP device-tree and GPIO mappings (research/touch-deep-dive.md:563-608). The A6X has its own
  SPI block, which is unknown, and the SPI3 claim is backed only by the Cascadia issue, not by this repo.
- Firmware and calibration blobs: firmware comes from the iPad 4's own IPSW, calibration is per panel
  (research/touch-deep-dive.md:633-636, 542-550; research/touch-re.md:946-955).
- The pongoOS pre-init idea (research/touch-deep-dive.md:682-697) targets A7+ and is unlikely to apply.

Caveat from this repo: whether the BCM5976 speaks Z2 on the wire is itself unproven
(research/touch-deep-dive.md:897-907; research/touch-re.md:295-318, 1001-1003). The A6X port inherits
that uncertainty.

On the 32-bit side: Cascadia reports touch working on the iPad mini 1 (A5). a6-handheld-linux has working
touch on the iPhone 5 with firmware uploaded from the phone's own iOS, but the controller chip is not
identified in the files read, and its transport (SPI1 at 0x32100000, specific GPIOs) is board wiring that
will not carry over.

### Estimated Effort

Medium (judgement). Justification: the protocol is documented from this repo's research (research/driver-gap.md
section 2), the two files contradict each other on details, and a 32-bit Apple device has a working touch stack
to compare against. The remaining work is an A6X SPI controller driver (the controller is unknown and not
covered by any finding), confirming the chip against the iPad 4's ADT and IPSW multitouch firmware, and
per-panel calibration. If the controller turns out not to be Z2, effort rises.

Sources:
- research/touch-deep-dive.md, research/touch-re.md (this repo)
- https://github.com/rzxvx/Project-Cascadia/pull/7 (mtcal spi3 change)
- https://github.com/lemonjesus/ipad-touch-screen
- https://github.com/AsahiLinux/asahi-installer/blob/main/asahi_firmware/multitouch.py

---

## 3. Display

### Hardware

- **Panel**: 2048x1536 Retina-class (issue #6). Panel vendor and model are not identified in any finding.
- **Controller**: `clcd` plus `edp` at 0x39500000 with a child LCD node in the p102ap DTS.
- **Backlight**: not identified. The only A6-family attempt (`kernel/platform/a6-backlight-trial.inc` in
  a6-handheld-linux, an LM3534 LED driver behind a DWI block at 0x3f700000) is a one-shot trial with no
  verified outcome, and it is iPhone 5 wiring.

### Linux Driver Status

**Status: no display driver. The framebuffer concept is proven on A6, not on A6X.**

- a6-handheld-linux `kernel/platform/fb-apple-a6.c` does not program the display. It reuses iBoot's live
  framebuffer, found through the Boot_Video fields of `boot_args`, and presents it via simpledrm (software
  rendering). The concept transfers; the code does not as written, because it is bound to the iPhone 5
  (hardcoded base 0xbf7aa000, 640x1136 geometry, compatible `apple,n42ap`). For the iPad 4 the geometry
  checks must change to 2048x1536 and the base must be read from `boot_args`.
- The a6-handheld-linux labwc/simpledrm desktop result is the author's own (`docs/test-results.md`), was not
  reproduced elsewhere, and was not tested on an iPad. Software-rendering performance at 2048x1536 is unknown.
- Cascadia's handoff loader also draws status on an iBoot framebuffer (0x9F6FC000, an A5 address).
- Not available on A6 either: backlight control (brightness fixed) and panel power management.
- This is the same approach research/driver-gap.md section 1 documents for the Air 2.

### Estimated Effort

Low, scoped to the iBoot framebuffer only (inference, not a general claim about display support). Justification:
no display controller programming is needed for this scope, only reading `boot_args` Boot_Video and adjusting
geometry. A native CLCD/eDP driver, panel power and backlight are excluded from this rating, and no finding
estimates them; for a native display driver the effort would be much higher and is unrated. The p102ap DTS only
carries raw ADT blobs for the display nodes.

Sources:
- https://github.com/landrucode/a6-handheld-linux (`kernel/platform/fb-apple-a6.c`)
- https://github.com/rzxvx/Project-Cascadia/issues/6

---

## 4. GPU

### Hardware

- **GPU**: PowerVR SGX554MP4 (Series5XT). The A5 iPad mini 1 has an SGX543MP2 (the iPad mini finding does
  not name it; the Cascadia reply compares to it); the iPhone 5 (A6) has an SGX543MP3.
- **ADT entry** (issue #6): `sgx,s5l8955x`, four cores listed at 0x35100000 and 0x3f10b000, IRQ 49 (0x31),
  with `dart-rt` and `dart-nrt` IOMMUs. Two addresses for four cores is not explained.
- A secondary source (AnandTech, search snippet only, not fetched) says the 554 doubles the ALUs per core
  (4 to 8 Vec4) relative to the 543, with the same texture and ROP units.

### Linux Driver Status

**Status: none. No SGX554 kernel or Mesa code exists in any source found.**

What exists is Cascadia's A5 stack, which targets the SGX543MP2 only:
- Kernel DRM driver `apple-sgx` (power, clocks, MMU, microkernel boot, queues, `/dev/dri/renderD128`).
- Mesa Gallium driver `sgx` with its own NIR-to-USSE compiler, giving GLES 1.1/2.0 and GL 2.1.
- The GPU microkernel firmware (`sgx543.fw`) is Apple/IMG's, extracted from the user's own IPSW; a
  replacement is "not on the plan". It is not open.
- Per-frame kernel data is computed by emulating iOS's kernelcache GPU kext under unicorn at pack build
  time, using captures from iOS 8.4.1 on A5.
- Known A5 limits: one render in flight, completion by polling (the interrupt was never seen to fire), no
  mipmaps, cube maps partial, one GPU address space, everything through debugfs as root.

The only statement that A6X can reuse this is the Cascadia owner's comment on issue #6 that the SGX554MP4 is
architecturally similar to the SGX543MP2, so much SGX543 work should carry over. It is an opinion, not
demonstrated by code. PR #7 added only a DTS and parser generalisation, and no GPU status for A6X appears in
the README.

Hard unknowns, stated plainly:
- **Four-core behaviour is unknown.** The A5 stack runs one render at a time on two cores, a core-1 fault
  needed a kernel workaround, and Cascadia documents no multi-core distribution policy. No source read says
  whether the microkernel splits work across four cores or whether the driver must.
- **Whether the SGX543 firmware runs on the 554 is unknown.** The A6X needs its own firmware extracted from an
  iPad 4 IPSW, probably a different microkernel build. No finding confirms the firmware format or load
  protocol matches.
- **Whether the shader compiler's output is valid on 8-wide ALUs is unverified.** The ISA is assumed
  identical, not checked.
- **DART (open question).** The A6X ADT lists `dart-rt` and `dart-nrt` IOMMUs for the GPU. No finding checks
  whether either reference project has a DART driver (it appears neither does), whether Cascadia's A5 GPU
  path programs or bypasses the equivalent, or whether non-GPU DMA on A6X needs DART setup. This is
  unresolved, and it may affect more than the GPU.
- The A6X register, clock and power-domain details are likely different (different ADT addresses and IRQ).
- Per-frame data needs A6X-specific captures and a retargeted kext emulation.
- a6-handheld-linux has no GPU support and gives no reason.

Other open work does not fill the gap. OpenPVRSGX forward-ports IMG's GPL kernel shim but userspace stays
proprietary blobs. The old libsgx work partially decoded USSE opcodes. Mesa's PowerVR Vulkan driver covers
Rogue and later, not Series5 (researcher's background knowledge, not a fetched source). Asahi's GPU work
targets a different architecture and does not apply. The absence of other SGX5 drivers is a negative result
from three searches, not proof.

### Estimated Effort

Very High. Justification: this is real driver and firmware bring-up, not a config change. The A5 stack is a
clean-room design tied to one firmware and one kext, reverse-engineered from iOS 8.4.1 traces on a different
core count, and its own notes list single-render polling as a limit. The DRM/Mesa skeleton and USSE tooling
lower the starting point, but the four-core question, the firmware question and the DART question are open.
Software rendering via simpledrm is the realistic fallback, which is what a6-handheld-linux ships. GPU
acceleration is a no-go for the initial roadmap.

Sources:
- https://github.com/rzxvx/Project-Cascadia (`devices/a5/docs/GPU.md`, `docs/research/p105-gpu.md`, `p105-mesa.md`)
- https://github.com/rzxvx/Project-Cascadia/issues/6
- https://www.anandtech.com/show/6426
- https://lists.goldelico.com/pipermail/openpvrsgx-devgroup/2021-November/000476.html
- https://libreplanet.org/wiki/Group:PowerVR_drivers

---

## 5. Wi-Fi

### Hardware

- **Chip (OPEN CONFLICT, not settled)**: Cascadia issue #6 says Broadcom BCM4334 over HSIC behind `usb-ehci0`
  ("matching the A5 setup"). a6-handheld-linux's report says the iPad 4 "uses a different Broadcom part and
  board". These two sources disagree and no finding resolves it. The BCM4334 claim is the issue author's own
  unverified statement. Anything below that assumes BCM4334 for the iPad 4 is conditional on this conflict.
- On the iPhone 5 (A6), a6-handheld-linux identifies BCM4334 rev 3, USB ID 0a5c:bd1a, EHCI at 0x36400000
  with HSIC port 4 hardcoded, AIC hwirq 0x0c, on a dedicated HSIC line. This is the iPhone 5, not the iPad 4.
- The chip must be confirmed from the iPad 4's ADT and IPSW.

### Linux Driver Status

**Status: working on A5 (Cascadia) and A6 (a6-handheld-linux), not tried on A6X.**

- Cascadia extracts `brcmfmac4334.bin` from the user's IPSW and Wi-Fi works on the iPad mini 1.
- a6-handheld-linux uses stock `brcmfmac` with HSIC wrapper handling (`kernel/platform/brcmfmac-a6-hsic.h`,
  `docs/wifi-transport.md`), with firmware and NVRAM from the phone's own iOS. The framing patch is generic to
  Broadcom-over-HSIC. Known fault with unknown cause: link stalls.
- Firmware and NVRAM are board-specific, so they come from the iPad 4 IPSW. The EHCI/HSIC wiring (base, port,
  IRQ) is read from the iPad 4 ADT.

### Estimated Effort

Medium (judgement, conditional on the chip conflict). Justification: two 32-bit Apple SoCs have working
BCM4334-over-HSIC Wi-Fi, so the driver path is proven for that chip. The work is new firmware and NVRAM
extraction, EHCI/HSIC bring-up with A6X addresses, and the link stalls seen on A6. If the iPad 4 chip differs
from BCM4334, as a6-handheld-linux suggests, effort rises and the firmware and driver path need re-evaluation.

Sources:
- https://github.com/landrucode/a6-handheld-linux (`docs/wifi-transport.md`)
- https://github.com/rzxvx/Project-Cascadia

---

## 6. Bluetooth

### Hardware

- **Link**: `uart3` at 0x32300000 (issue #6). The chip is not stated; a BCM4334-family combo part is the
  likely candidate given section 5, but that is inference and inherits the Wi-Fi chip conflict.
- UART assignment: the console UART differs by source (a6-handheld-linux: ttySAC0 at 0x32600000, iPhone 5;
  Cascadia: ttyAPL0 on UART0). The Bluetooth uart3 claim must be checked against whichever UART is chosen as
  the console, to avoid a clash.

### Linux Driver Status

**Status: working on A5, not implemented on A6, not tried on A6X.**

- Cascadia extracts `BCM4334B0.hcd` from the IPSW and lists Bluetooth as working on the iPad mini 1.
- a6-handheld-linux lists Bluetooth as "Not implemented" with no reason given.
- The p102ap DTS summary showed no Bluetooth node; this is unconfirmed against the full file.

### Estimated Effort

Medium (judgement). Justification: the A5 case shows the btbcm/hci_bcm path works with extracted patch RAM, but no finding
gives the A6X uart3 reset, wake or clock wiring, and the nearest A6 neighbour never attempted Bluetooth, so
there is no same-family comparison for the board wiring.

Sources:
- https://github.com/rzxvx/Project-Cascadia/issues/6
- https://github.com/landrucode/a6-handheld-linux (`STATUS.md`)

---

## 7. Storage / NAND

### Hardware

- No finding identifies the iPad 4's NAND controller. No model is assumed here.
- The A6X predates ANS1. research/driver-gap.md section 10 (this repo, not part of the external findings)
  describes the ANS1 storage co-processor (an RTKit core with an AKF mailbox) and its Linux driver `asp.c`
  (HoolockLinux `ans1` branch); that driver's Kconfig `APPLE_ASP` covers "Apple A7, A8, A8X SoCs". The
  "A6X predates ANS1" point is inference from that, not a finding about A6X.

### Relevance of the A8X storage findings

**Not relevant to A6X.** The section 10 findings about ANS1, the `asp` driver, RTKit protocol v10, and the
`apple,s5l8960x-ans` / `t7000-ans` / `t7001-ans` bindings do not apply: the A6X has no ANS1 co-processor and
`APPLE_ASP` does not list it. Two background points from section 10 are general to Apple NAND (proprietary
FTL, and a hardware AES engine with UID-derived keys that keeps existing iOS data unreadable), but no finding
establishes that A6X has exactly this shape, so they are not asserted here.

### Linux Driver Status

**Status: no Linux NAND or storage driver identified for A6X.**

The sources show iBoot-mediated access instead. Cascadia's PC-less route
(`devices/a5/scripts/patch-ibec-upgrade.py`, `devices/a5/docs/research/p105-pcless-boot.md`) reuses iBoot's
own NAND, LwVM and HFS+ stack: the patched iBEC `upgrade` command mounts the "System" HFS+ partition
(unencrypted, writable from jailbroken iOS) and loads `/devicetree`, `/ramdisk` and `/kernelcache` from it.
Linux itself never drives the NAND. This is A5-specific in detail (22 patched bytes at iBoot-2261 P105
addresses, partition names, LwVM layout), and the doc says packaging is not finished upstream. An A6X needs
re-derivation against its own iBoot, including the NAND and LwVM layout.

Both Linux-on-Apple-32-bit projects boot tethered from RAM: a6-handheld-linux writes nothing to NAND, a power
cycle returns to iOS, and each boot needs a host with checkm8 run by hand. Where a rootfs lives is therefore
an open design choice (initramfs, USB networking or NFS), not a solved one.

### Estimated Effort

High (inference, consistent with the summary matrix). This rating rests on absence of evidence (no source
names an A6X NAND controller or a Linux driver for it) and on this repo's section 10, not on a measured
finding. A native storage driver starts from reverse engineering. The only demonstrated alternative
(iBoot-mediated boot from the System partition) exists only for A5 P105, is unfinished upstream, and needs
fresh patch offsets and layout analysis for A6X. RAM-only boot (initramfs, USB networking, NFS root) needs no
storage driver and is the current practical path, but it gives no persistence. Storage is the second-hardest
item in the matrix and decides persistence; it is deprioritised in the Overall Assessment, not dropped.

Sources:
- research/driver-gap.md section 10 (ANS1 and `asp`, A7-A8X only)
- https://github.com/rzxvx/Project-Cascadia (`devices/a5/docs/research/p105-pcless-boot.md`)
- https://github.com/landrucode/a6-handheld-linux (`README.md`)

---

## 8. Audio

### Hardware

- **iPad 4 codec**: not identified in any finding.
- On the iPhone 5 (A6), a6-handheld-linux uses a Cirrus Logic CS42L65 controlled over SPI3 with chip select on
  GPIO 87, an "iis" block plus PMGR gates, and a route switch (`kernel/platform/a6-audio-codec.inc`).

### Linux Driver Status

**Status: working on A5 (speakers, Cascadia) and on A6 (speaker and microphone, a6-handheld-linux). None on A6X.**

- The a6-handheld-linux audio is replayed from stock firmware sequences ("EmbeddedAudio 80a3973c", via
  `scripts/prepare-a6-speaker-sequence.py` and `scripts/prepare-a6-codec-sequence.py`), not a mainline codec
  driver. The finding states the codec and wiring are N42-specific and the iPad 4 has different chips and pin
  assignments.
- The p102ap DTS has `i2s` nodes but no identified codec or amplifier.
- `a6-audio-alsa.inc` and the sequence scripts were not read in full.

### Estimated Effort

High (judgement). Justification: the A6X codec is unidentified, and the only A6-family working audio is a sequence replay
tied to iPhone 5 hardware (CS42L65 on SPI3, GPIO 87). The work is codec identification from the iPad 4 ADT,
extracting and replaying its stock sequences, and writing the A6X I2S and routing setup. Audio is deprioritised
for the first milestones.

Sources:
- https://github.com/landrucode/a6-handheld-linux (`kernel/platform/a6-audio-codec.inc`)
- https://github.com/rzxvx/Project-Cascadia (README, status table)

---

## 9. USB

### Hardware

- **Host**: EHCI and OHCI (the p102ap DTS has `usb-ehci`, `usb-ohci` and OTG PHY control nodes).
- **Wi-Fi link**: HSIC behind `usb-ehci0` (section 5).
- **Device/OTG**: a6-handheld-linux drives the DWC2 core for gadget mode. The finding says this is likely the
  same IP block on A6X, not verified.

### Linux Driver Status

**Status: working on A5 (Cascadia) and A6 (a6-handheld-linux), not tried on A6X.**

- Cascadia ships `drivers/phy/phy-apple-s5l-usb.c` (A5), and its loader re-programs the OTG PHY at 0x36000000
  and restores PMGR clock gates (0x3F101080, 0x3F101084, 0x3F101098), because iBEC's `prepare_and_jump` leaves
  USB off. Those are A5 addresses.
- a6-handheld-linux patches mainline `dwc2` with `apple,s5l8950-dwc2` (DMA off, OTG/LPM off, UTMI 16-bit PHY,
  FIFO sizes 512/128/128, an L3-reinit fix in `kernel/patches/a6-dwc2-l3-reinit.patch`). Its PHY driver
  `phy-apple-a6-usb.c` uses unexplained magic values (0x749, 0x2ff3, 0x200). Known fault with unknown cause:
  large phone-to-host transfers stall (`docs/usb-observation.md`).
- checkm8_bootkit carries an A6X entry (CPID 0x8955, load address 0x10000000, load size 0x60000); its source
  cannot confirm the A6X ROM offsets work on hardware. a6-handheld-linux demonstrates the exploit path only on
  A6; there is no A6X hardware evidence.

### Estimated Effort

Medium (judgement). Justification: patches and PHY drivers for the same IP exist on A5 and A6, so the A6X work is
re-deriving PHY register values and base addresses from the iPad 4 ADT. The unexplained PHY magic values and
the unresolved A6 transfer stalls mean this cannot be rated Low without hardware verification, and USB was
trial and error in both reference projects, so it is a higher-risk Medium.

Sources:
- https://github.com/landrucode/a6-handheld-linux (`kernel/patches/`, `kernel/platform/phy-apple-a6-usb.c`)
- https://github.com/rzxvx/Project-Cascadia (`devices/a5/pongo/linux_boot_start.S`)
- https://github.com/NyanSatan/checkm8_bootkit (`src/libbootkit/config.h`)

---

## Boot Chain Context

Not a subsystem, but it gates every row above because nothing can be tested without a boot path. No A6X hardware
evidence exists for any step below; they are a reasoned starting point, not proven coverage.

- **Tethered, RAM-only boot.** Both reference projects need a host running checkm8 on every boot, and a power
  cycle returns the device to iOS. Cascadia's PC-less NAND route is unfinished upstream and A5-specific.
- checkm8_bootkit supports S5L8955X with dedicated ROM offsets and boots a raw iBSS. Constraints: the raw
  unpacked image must start with 0xEA00000E and fit in loadsize 0x60000 (384 KiB) minus the payload. The tool
  does no signature patching and does not extract from an IPSW, so patched, decrypted iBSS and iBEC images are
  mandatory inputs, and the 384 KiB limit applies to them. The ROM offsets are untested on hardware per the
  source. That checkm8 runs from a PC host for A6X is the normal route from general knowledge, not shown by any
  A6X evidence.
- Firmware source and iOS version: the A6X firmware may use a different iOS version than a6-handheld-linux's
  iPhone 5 ("likely 8.4.1 or 10.3.x" per its docs). This changes the Mach-O layout, keys and load addresses.
  Keys and firmware inputs (for example via Legacy-iOS-Kit) must be resolved first, and no extraction guide
  exists.
- Cascadia's A5 exploit path (Pi Pico, checkm8-a5) and kDFU path (EverPwnage tfp0, iOS 8.0 to 9.3.6) are
  A5-specific. The kDFU path is a no-PC entry, but it would need an A6X-specific jailbreak. The iBSS/iBEC patch
  addresses and the iBEC auto-go hook offsets are specific to iBoot-2261 P105 8.4.1, so A6X needs fresh offsets
  for its own iBEC.
- The a6-handheld-linux chain (patched iBSS and iBEC, Apple's own DeviceTree img3, an IMG3 kernelcache with a
  one-instruction entry patch to a handoff stub, `bootx`) is the closest known recipe, for the iPhone 5 (A6, not
  A6X). Its Mach-O layout, addresses and IV/key are iPhone 5 and iOS 8.4.1 specific. Its `BUILDING.md` says the
  scripts were never run from a fresh checkout, and the DFU-with-IBFL-0x1b-then-Recovery flow comes from the
  iPhone 5 (N42) and is unverified for A6X.
- Kernel size bound: in a6-handheld-linux the payload sits at Mach-O vm 0x80100000 and the handoff cave is at
  0x80cbb38c, so the zImage plus an embedded initramfs is bounded. Other offsets apply under feature flags, so
  the bound is approximate.
- No A6X loader, kernel config (`config/p102ap.config` does not exist) or boot log was found in Cascadia. The
  tree listing was truncated, so this is not conclusive. Cascadia's loader lives in a directory named `pongo/`
  and its README mentions a pongo module; the findings show only that A5 and A6 chains use iBSS/iBEC, so
  whether pongoOS applies to A6X is not established either way by any source read.
- Kernel version: Cascadia pins v6.12. a6-handheld-linux's kernel commit is pinned in its build scripts and not
  stated in the findings. Which mainline base to use is an open question for the NixOS `buildLinux` config.
- Battery hazard: a6-handheld-linux reports that one night the phone discharged after losing the host, and that
  "the charger code cannot stop charging if the kernel hangs". This is a hazard on the larger iPad battery and
  must be treated as a risk of any unattended run.
- Nix side (this repo): `crossSystem` for armv7l is `armv7l-unknown-linux-gnueabihf` (the
  `armv7l-hf-multiplatform` example). There is no official binary cache for armv6/armv7 native builds, and
  the musl armv7l triple has no cited example. `buildLinux` needs `defconfig = "multi_v7_defconfig"` set
  explicitly and `ARM64_16K_PAGES` removed. An appended-DTB zImage is likely needed for the handoff. None of
  this was evaluated with `nix build`.

Sources:
- https://github.com/NyanSatan/checkm8_bootkit
- https://github.com/rzxvx/Project-Cascadia
- https://github.com/landrucode/a6-handheld-linux (`BUILDING.md`, `scripts/build-a6-kernelcache.sh`)
- https://wiki.nixos.org/wiki/NixOS_on_ARM
- https://github.com/NixOS/nixpkgs/blob/master/lib/systems/examples.nix

---

## Overall Assessment

The nearest prior art is a pair of 32-bit Apple SoC projects (A5 iPad mini 1, A6 iPhone 5) that provide a
reasoned starting point for the A6X's boot environment. Neither targets the A6X, and the A6 project's build
has not been reproduced from a fresh checkout. Low-level SoC blocks (AIC, timer, USB, Wi-Fi bus) are the most
reusable, subject to the verification items below. Board-level peripherals (touch bus, audio codec, display
backlight, PMU) must be re-derived from the iPad 4's own ADT and IPSW. The GPU (SGX554MP4) and native storage
have no usable prior art for A6X.

Priority and deprioritisation:
- GPU (Very High): no-go for the initial roadmap; software rendering via the iBoot framebuffer is the fallback.
- Storage (High): deprioritised. RAM-only tethered boot is the working assumption, which means no persistence.
- Audio (High): deprioritised.
- Display (Low): the rating covers only the iBoot framebuffer, not a native display driver.

Open verification items, in order:
1. Extract the iPad 4's own DeviceTree img3 and confirm every address in this document (AIC, SPI3, uart3,
   EHCI, PHY) against it, because they come from one unverified issue. Include the AIC register map comparison,
   the PMGR SMP offsets, the CNTFRQ value, the watchdog, and the DART nodes.
2. Resolve the two source conflicts: the Wi-Fi chip (Cascadia says BCM4334, a6-handheld-linux says a
   different Broadcom part) and the touch controller part (unconfirmed, plus the contradictions between
   research/touch-re.md and research/touch-deep-dive.md).
3. Identify the A6X SPI controller; the A8X SPI controller work does not carry over.
4. Clone Project-Cascadia and run `grep -ril "8955\|p102" .` to close the truncated-tree gap, and read
   `devices/a5/dts/p102ap.dts` in full.
5. Read the unread a6-handheld-linux files (`scripts/build-a6-zimage.sh`, the touch, audio and Wi-Fi `.inc`
   files) before committing to a design.
6. Decide the iOS version and firmware source, and the mainline kernel base.
