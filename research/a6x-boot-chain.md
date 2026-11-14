# A6X (iPad 4) boot chain

Status: research draft. No A6X kernel bring-up has been done and no A6X boot log exists. Every A6X statement below is inference from A6 (iPhone 5) and 32-bit iPad references, unless marked otherwise.

## 0. Scope and divergence from pongoOS

The target is the iPad 4 (A6X, 32-bit ARMv7 "Swift" cores, board `p102ap` in the findings). The rest of this repo targets the iPad Air 2 (A8X) through checkm8, then pongoOS, then Linux. That chain does not carry over to A6X.

- pongoOS targets 64-bit A7-A11 devices. A6X is 32-bit. This is general knowledge and is not in the findings.
- The findings show the two A6/A5-era references use the iBSS/iBEC chain, not a pongoOS chain:
  - checkm8_bootkit loads and patches an iBSS.
  - a6-handheld-linux patches iBSS/iBEC for the iPhone 5.
- Project Cascadia (32-bit iPad Linux) names its loader directory `pongo/`, and its README mentions a pongo module. The claim "pongoOS is not used for A6X" therefore needs care. The cited evidence is that Cascadia's loader sits under a directory named `pongo/` and its README mentions a pongo module. Whether that loader is pongoOS itself or only borrows its name or interface is not resolved in the findings. The working assumption is the iBSS/iBEC patch route, and the pongoOS question stays open (section 9).

## 1. What exists and what does not

Exists in this repo:
- An A6X device tree source (DTS). Its header still reads iPad3,5, and a stale iPad2,5 header is also noted (section 9).
- A parser generalization for the device tree tooling.
- A hardware map.
- A checkm8_bootkit config entry listing A6X.

Does not exist:
- Any A6X kernel bring-up.
- Any A6X boot log.
- Any hardware evidence that the checkm8 offsets for A6X work.

Evidence strength:
- a6-handheld-linux targets the iPhone 5 (S5L8950X, A6), not A6X.
- Its BUILDING.md says the scripts were never run from a fresh checkout.
- Its "desktop booted" result (labwc on simpledrm) is documented only in the author's own `docs/test-results.md`. It is unreproduced and untested on any iPad.
- Statements that A6X behaves like A6 are this research's inference. The a6-handheld repo never mentions A6X or the iPad. The "same Swift core" claim is inferred and unverified.
- Cascadia has no A6X loader or boot code.
- checkm8_bootkit's A6X ROM offsets are unverified on hardware.

Together the references give a reasoned starting point, not coverage of the boot path.

## 2. Stage 1: checkm8 entry

- Upstream: checkm8_bootkit (config lists A6X); a6-handheld-linux demonstrates the flow on A6 only.
- A PC host puts the device in DFU mode and runs checkm8. This is the normal route according to Cascadia and general knowledge. It has no A6X hardware evidence.
- a6-handheld's iPhone 5 (N42) flow reaches DFU with IBFL 0x1b, then Recovery. This is unverified for A6X and is not a pass condition until measured.
- No-PC entry paths exist upstream but do not transfer directly:
  - Pi Pico entry is A5-only.
  - kDFU via an EverPwnage tfp0 jailbreak would need an A6X-specific jailbreak.
  - Neither is a planned route.
- a6-handheld contains a docstring saying it needs "no exploit". This is inaccurate for the boot path and should be ignored.

## 3. Stage 2: iBSS patching

- Upstream: checkm8_bootkit loads the iBSS at 0x10000000. This is the address where the tool places the iBSS image. It is not a DRAM base.
- The tool does no signature patching and does not extract from an IPSW. A patched, decrypted iBSS is a mandatory input.
- Constraints from checkm8_bootkit:
  - The raw unpacked image must start with the header word 0xEA00000E.
  - The image must fit within loadsize 0x60000 (384 KiB), minus the payload. The limit applies to the patched iBSS and iBEC.
- A6X difference: the offsets are unverified for A6X, and Cascadia's offsets are specific to "iBoot-2261". Offsets must be re-derived against the A6X firmware actually used.

## 4. Stage 3: iBEC patching

- Upstream: a6-handheld-linux patches the iBEC (iPhone 5). Cascadia's PC-less NAND route (an iBEC "upgrade" patch) is unfinished upstream.
- Cascadia's NAND/LwVM layout would need re-derivation for A6X.
- The same 384 KiB image limit applies to the iBEC under checkm8_bootkit.
- Firmware source: A6X may ship a different iOS version than the references. a6-handheld says "likely 8.4.1 or 10.3.x". The version changes the Mach-O layout, the decryption keys and the load addresses. The firmware keys are therefore unresolved. Legacy-iOS-Kit is a possible firmware input, and no extraction guide exists.

## 5. Kernel and DTS packaging

- Cascadia pins Linux v6.12. a6-handheld's kernel commit is "pinned in build scripts" and is not stated. The mainline base for the NixOS `buildLinux` config is an open question.
- In a6-handheld the payload sits at Mach-O vm 0x80100000 and the handoff cave is at 0x80cbb38c. zImage plus an embedded initramfs (the Nix initramfs) is therefore size-bounded. The bound is approximate, because the findings say other offsets apply under feature flags.
- a6-handheld's `build-a6-zimage.sh` was not read. The 1 GiB versus 512 MiB RAM build discrepancy between the references is unexplained.
- The DTS from this repo is the input. RAM size in the DTS must be checked: the 512 MiB figure is a Cascadia placeholder marked "patched at boot". The 1 GiB figure for the iPad 4 comes from the a6-handheld finding.

## 6. Handoff

- The handoff passes control to the kernel and DTS from the patched boot stage. a6-handheld uses a handoff stub at the cave described above.
- Cascadia's loader disables the watchdog (0x3F103020) before the jump. a6-handheld's DTS lists a watchdog at 0x0f103020, but its handoff stub does not mention disabling it. Whether A6X needs the watchdog disabled is an open question (section 9).
- Secondary cores: a6-handheld releases CPU1 through PMGR offsets 0x214 and 0x220. These are unverified for A6X. The CNTFRQ 24 MHz assumption is also unverified. SMP bring-up was trial-and-error for both references.

## 7. First expected result (hypothesis)

Not observed. If the chain works, the expected order is:

1. Framebuffer colour stages from the iBoot framebuffer (2048x1536). a6-handheld hardcodes the base and geometry.
2. simpledrm text console.
3. A USB gadget shell.

The USB PHY magic values used by a6-handheld (0x749, 0x2ff3, 0x200) are unexplained, so USB may need trial and error.

## 8. Tethered, RAM-only boot, and hazards

- The boot is tethered and RAM-only. Both references need a host running checkm8 on every boot. A power cycle returns the device to iOS. Nothing is written to NAND by the planned route.
- The rootfs lives in the initramfs or on USB/NFS. No persistent storage is planned. Persistent storage on A6X predates ANS1 (an inference, not in the raw findings), and NAND layout would need re-derivation.
- Battery hazard, reported by a6-handheld: one night the phone discharged after losing the host, and "the charger code cannot stop charging if the kernel hangs". On the larger iPad battery this is a risk. Do not leave a tethered session unattended or on a hung kernel while connected to power.

## 9. Open questions

1. Board name: every finding says `p102ap`. The name P103 appears nowhere in the findings and is not asserted here. Whether the DTS header iPad3,5 (a cellular iPad 4 variant) versus the stale iPad2,5 header matters, and which of the three iPad 4 model numbers `p102ap` covers (including Wi-Fi-only variants), is unresolved.
2. RAM: the real DRAM base and size for A6X are unconfirmed. Candidates are 0x80000000 as a base, a 512 MiB Cascadia placeholder, and 1 GiB from the a6-handheld iPad 4 finding. This is separate from the 0x10000000 address where checkm8_bootkit loads the iBSS.
3. Interrupt controller: Cascadia's `aic,1` at 0x3f200000 and a6-handheld's own AIC may be different drivers. a6-handheld's register map (EVENT 0x2004, TARGET_CPU 0x3000, and so on) must be compared with the iPad 4's ADT before any reuse.
4. UART console: ttySAC0 at 0x32600000 (a6-handheld, iPhone 5) versus ttyAPL0 on UART0 (Cascadia). The Bluetooth UART claim (uart3 at 0x32300000, Cascadia) must be checked against whichever console UART is chosen.
5. Touch: the controller IC is unconfirmed. `touch-re.md:533` states BCM5976 for the iPad 3 as fact, while `touch-deep-dive.md:268-270` says it is unconfirmed. The 0xD9 report offsets disagree between the two files. "Z2F13" is an iOS driver name, not a part number. The nearest 32-bit evidence is the iPad 3 / lemonjesus material. The A6X SPI controller is unknown, and the A8X one is not reusable. Cascadia says the iPad 4 uses spi3, while a6-handheld's iPhone 5 touch uses SPI1 with an unidentified controller chip.
6. Wi-Fi chip: only Cascadia issue #6 says BCM4334 for the iPad 4, and it is the author's unverified claim. a6-handheld says the iPad 4 uses a different Broadcom part and board.
7. Watchdog: whether A6X needs it disabled before handoff (section 6).
8. DART: the A6X ADT lists dart-rt and dart-nrt IOMMUs for the GPU. No finding shows that either reference has a DART driver, or whether non-GPU DMA needs one.
9. Firmware version and keys: iOS 8.4.1 versus 10.3.x, and where the keys come from (section 4).
10. Kernel base version (section 5).
11. Whether Cascadia's `pongo/` loader is pongoOS or only borrows the name (section 0).
12. Whether the PMGR CPU1 offsets, the CNTFRQ value and the USB PHY values hold on A6X (sections 6 and 7).

## 10. Provenance

- Sources: the Project Cascadia and a6-handheld-linux repositories, checkm8_bootkit, and this repo's research notes.
- A6X statements are the researcher's inference unless a hardware observation is cited. None is cited.
- Judgements such as driver difficulty ratings elsewhere in `research/` rest on absence of evidence and should be read as inference.
- GPU: no open driver path exists. A6X graphics is limited to software rendering over the iBoot framebuffer, with unknown performance.
