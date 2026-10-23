# Feasibility Assessment: NixOS on iPad Air 2

Synthesis of landscape, hardware, boot chain, and driver gap research.
Assessment conducted February 2026.

## Verdict: Feasible with Known Limitations

Booting NixOS on iPad Air 2 (A8X) is feasible. Linux has already booted on this exact
hardware (Konrad Dybcio, June 2022, kernel 5.18). The boot chain is proven and actively
maintained. The question is not "can it boot?" but "how usable can it be?"

## Milestone Assessment

### M1: Boot to Serial Console
**Status: Achievable (proven)**

All components exist:
- checkm8 exploit: stable, A8X supported (gaster, Achilles)
- pongoOS: actively maintained (palera1n fork, Jan 2026)
- Linux kernel: device trees merging into mainline (Linux 6.13+, Nick Chan patches)
- initramfs: standard Linux, no special work needed

Effort: Days. Primarily integration work — building kernel with correct config, compiling
device tree, preparing initramfs, scripting the boot sequence.

### M2: Framebuffer Display + USB Networking
**Status: Achievable (proven)**

- simplefb/simpledrm: working, depends on iBoot display initialization (already set up
  before pongoOS loads)
- DWC2 USB gadget: driver exists in mainline, needs device tree integration
- USB Ethernet (RNDIS/ECM): standard Linux gadget, enables SSH from host

Effort: Days to a week. The display works via simplefb. USB gadget mode needs platform
glue and device tree nodes for the DWC2 controller.

### M3: WiFi Networking
**Status: Achievable with firmware extraction**

- BCM4354: brcmfmac driver in mainline, chip ID supported
- Firmware: must extract from iOS IPSW (documented process, done for iPhone 7)
- NVRAM: board-specific calibration file needed (Murata 339S02541 module)
- SDIO bus: needs device tree configuration

Effort: 1-2 weeks. The driver works. Firmware extraction is documented. Main unknowns
are NVRAM format and any Apple-specific SDIO quirks.

### M4: Touch Input
**Status: Requires reverse engineering**

- BCM5976 over SPI: no Linux driver, no public protocol documentation
- Reference: bcm5974 USB driver (MacBook trackpads) documents report format for related
  chips, but uses different transport
- Reference: hx-touchd from Project Sandcastle handles iPhone 7 touch (different chip)
- SPI bus identification needed from iOS device tree or RE

Effort: 2-6 weeks. Requires logic analyzer captures or iOS kernel instrumentation to
decode the SPI protocol. The BCM5976 is used across many Apple devices (2012-2017), so
a driver would have broad impact.

### M5: GPU Acceleration
**Status: Blocked (long-term research)**

- PowerVR GXA6850: Apple-customized 8-cluster Series 6XT
- Mesa PVR Vulkan driver: exists but only partially supports GX6250 (smaller variant)
- GXA6850 not listed in Mesa, no kernel DRM backend for Apple A8X
- Three separate problems: kernel DRM driver, Mesa compiler backend, Apple platform glue

Effort: Months to years. Software rendering (llvmpipe) is the practical alternative.
A usable desktop is possible with llvmpipe at the native 2048x1536 resolution, though
performance will be limited to basic window management and text-based applications.

### M6: Audio
**Status: Requires significant RE**

- Cirrus Logic 338S1213: unknown public model, no Linux driver
- MAX98721 amplifier: no upstream driver
- A8X audio DMA engine: proprietary, undocumented
- Three-layer driver stack with no existing components

Effort: 4-8 weeks minimum. Audio is a quality-of-life feature, not critical for a
workstation use case (USB audio adapters are an alternative via USB host mode).

## Critical Path

```
M1 (serial console) ──► M2 (display + USB net) ──► M3 (WiFi) ──► M4 (touch)
       ▼                        ▼
  NixOS rootfs              SSH access
  generation                from host
```

M1 through M3 are achievable with existing drivers and documented techniques.
M4 (touch) is the gate for standalone use without an external keyboard.

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Boot chain breaks with iOS update | Low | Low | checkm8 is iOS-version-independent |
| Device tree patches rejected from mainline | Medium | Low | Maintain out-of-tree patches |
| BCM4354 firmware extraction fails | Low | High | Use USB networking as fallback |
| BCM5976 touch protocol too complex to RE | Medium | High | Use USB keyboard/mouse via OTG |
| Kernel panics during bring-up | High | Low | Expected; iterative debugging via serial |
| PMIC misconfiguration damages hardware | Low | Critical | Rely on iBoot initialization, do not touch PMIC |
| 2GB RAM insufficient for NixOS | Medium | Medium | Minimal NixOS config, swap over USB, use lightweight DE |

## Honest Assessment

**What is realistic:**
- Boot NixOS to a graphical login with framebuffer display
- SSH access over USB and WiFi
- Lightweight desktop environment (sway, i3, or similar) with software rendering
- Web browsing via text-based browser or lightweight GUI browser
- Terminal workstation use (development, writing, SSH client)

**What is unlikely without major RE effort:**
- Touch input (needed for standalone tablet use)
- Hardware-accelerated graphics
- Audio output (without USB audio adapter)
- Internal storage access (a WIP ANS1 driver exists in HoolockLinux, see driver-gap.md)

**What is not feasible:**
- Untethered boot (checkm8 is permanently tethered)
- Touch ID / biometric authentication
- Camera
- Cellular data (LTE model)

## NixOS-Specific Considerations

### Cross-Compilation

NixOS supports aarch64 cross-compilation. The flake can target `aarch64-linux` from an
`x86_64-linux` host. Key considerations:

- 16KB page size: the kernel must be compiled with `CONFIG_ARM64_PAGE_SHIFT=14`. Standard
  NixOS aarch64 builds use 4KB pages. A custom kernel package is required.
- initramfs generation: NixOS can generate a complete system image as an initramfs using
  `config.system.build.initialRamdisk` or a custom derivation.
- Binary cache: Hydra builds standard aarch64-linux packages, but 16KB page binaries may
  need local compilation for some packages.

### System Image Strategy

Internal NAND has no driver in this repository's kernel, so the entire NixOS system runs from RAM:

**Option A: Fat initramfs**
- Pack the complete NixOS closure into an initramfs (cpio archive)
- Simple, self-contained, but limited by 2GB RAM
- A minimal NixOS system with sway and basic tools: ~500MB compressed, ~1.5GB uncompressed
- Leaves ~500MB for runtime use — tight but workable

**Option B: NFS root**
- Minimal initramfs with networking, mount NixOS root over NFS from host machine
- More storage available, but requires network connection
- USB Ethernet or WiFi must work

**Option C: USB storage root**
- Boot from initramfs, pivot root to USB flash drive via Lightning OTG adapter
- Best of both: full storage, no network dependency
- Requires working USB host mode and Lightning-to-USB adapter

Recommended: Start with Option A (fat initramfs) for initial bring-up, transition to
Option C (USB storage) for daily use.

### Declarative Configuration Value

NixOS's declarative model is well-suited to this project:
- Reproducible builds: the exact system image is defined by the flake
- Iterative development: change config, rebuild, re-flash — fast feedback loop
- Version control: entire system configuration lives in git
- Rollback: previous system images are trivially reproducible

## Recommended Roadmap

### Phase 1: First Boot (1-2 weeks)
- Build kernel with A8X device tree and correct config
- Generate minimal NixOS initramfs
- Script the full boot sequence (checkm8 → pongoOS → load_linux.py)
- Achieve serial console output
- Achieve framebuffer display output

### Phase 2: Networking (1-2 weeks)
- USB gadget Ethernet (RNDIS/ECM) for SSH access
- WiFi via brcmfmac with extracted firmware
- NFS root or USB storage root for expanded filesystem

### Phase 3: Usable Desktop (2-4 weeks)
- Lightweight window manager (sway or cage) with llvmpipe
- On-screen keyboard (if touch is not yet working)
- External keyboard/mouse via USB OTG
- Basic applications (terminal, browser, editor)

### Phase 4: Touch + Polish (4-8 weeks)
- BCM5976 touch controller reverse engineering
- Bluetooth via btbcm
- Battery monitoring via BQ27546
- Power management improvements

### Phase 5: Long-term (ongoing)
- GPU acceleration investigation (Mesa PVR)
- Audio codec RE
- Upstream contributions (device tree improvements, drivers)

## References

- Konrad Dybcio iPad Air 2 Linux boot: https://hackaday.com/2022/06/12/boot-mainline-linux-on-apple-a7-a8-and-a8x-devices/
- Nick Chan device tree patches: https://lore.kernel.org/lkml/20240925071939.6107-3-towinchenmi@gmail.com/T/
- pongoOS: https://github.com/checkra1n/PongoOS
- Project Sandcastle: https://github.com/corellium/projectsandcastle
- HoolockLinux: https://github.com/HoolockLinux
- Mesa PVR driver: https://docs.mesa3d.org/drivers/powervr.html
- postmarketOS iPhone 7: https://wiki.postmarketos.org/wiki/Device:iPhone_7/7+
