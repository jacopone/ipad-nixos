# Landscape Analysis: Linux-on-iPad/iPhone Projects

Analysis of all existing projects relevant to booting Linux on iPad Air 2 (A8X).
Research conducted February 2026.

## 1. checkm8 — Bootrom Exploit

**Purpose**: Permanent, unpatchable bootrom (SecureROM) exploit enabling arbitrary code execution on Apple A5-A11 devices during DFU boot.

**Creator**: axi0mX, disclosed September 2019. CVE-2019-8900.

**How it works**:

The exploit targets the USB DFU (Device Firmware Upgrade) stack in Apple's SecureROM. The attack sequence:

1. Device enters DFU mode (triggered via physical button combination while powered off).
2. Attacker sends a USB Setup Stage request, begins data transfer, then issues a DFU abort to force DFU restart.
3. On DFU re-entry, the device frees the IO buffer but does not reset the global pointer to that buffer (use-after-free).
4. Heap feng-shui (heap grooming) ensures the next DFU iteration allocates its IO buffer at a different address, leaving the freed buffer accessible.
5. On certain SoCs (A9X, A10, A10X, A11), endpoint stalling leaks request objects that persist through DFU shutdown.
6. A `usb_device_io_request` object is overflowed, overwriting its callback function pointer to redirect execution to attacker payload.
7. Arbitrary code runs at SecureROM privilege level.

**Why it is unpatchable**: The vulnerable code resides in hardware-burned SecureROM (BootROM). No software update can modify it. Only a hardware revision fixes the bug.

**Supported devices** (A5 through A11):

| Chip | iPad models |
|------|------------|
| A5 | iPad 2 |
| A5X | iPad 3rd gen |
| A6X | iPad 4th gen |
| A7 | iPad Air 1, iPad Mini 2/3 |
| A8 | iPad Mini 4 |
| A8X | **iPad Air 2** (primary target) |
| A9X | iPad Pro 9.7", iPad Pro 12.9" 1st gen |
| A10 | iPad 7th gen |
| A10X | iPad Pro 10.5", iPad Pro 12.9" 2nd gen |
| A11 | (no iPads, iPhone 8/X only) |

Also supports: iPhone 5S through iPhone X, iPod Touch 6th/7th gen, Apple TV HD, Apple TV 4K 1st gen.

**Current status (2026)**: Fully stable and permanent. Primary tools implementing the exploit:
- `ipwndfu` (axi0mX's original Python tool)
- `gaster` (C implementation)
- `checkm8-a5` (A5-specific implementation)
- Used by checkra1n and palera1n jailbreak tools

**Limitations**: Requires physical USB access. Does not bypass Secure Enclave, Touch ID, or device PIN. Tethered (must re-exploit on each boot).

**Relevance to iPad Air 2 (A8X)**: Directly supported. The A8X is vulnerable to checkm8, providing the foundation for the entire boot chain.

**License**: Various open-source implementations (ipwndfu is MIT, gaster is MIT).

Sources:
- https://theapplewiki.com/wiki/Checkm8_Exploit
- https://alfiecg.uk/2023/07/21/A-comprehensive-write-up-of-the-checkm8-BootROM-exploit.html
- https://habr.com/en/companies/dsec/articles/472762/
- https://blog.elcomsoft.com/2022/06/checkm8-extraction-the-ipads-ipods-and-tvs/

---

## 2. checkra1n — Jailbreak Built on checkm8

**Purpose**: Semi-tethered jailbreak for checkm8-vulnerable devices. Provides root filesystem access on iOS.

**Current status (2026)**:
- Official checkra1n: supports iOS 12.0 through 14.8.1 (latest build 0.12.4 beta)
- No official support for iOS 15+
- Development has slowed significantly; no major releases since 2021

**Supported iOS versions**: iOS 12.0 - 14.8.1 (official). The tool runs on macOS and Linux host machines.

**Relevance to Linux booting**: checkra1n is the delivery mechanism for pongoOS. The checkra1n exploit chain loads pongoOS into memory on the target device, which then provides the environment for booting Linux. Even though checkra1n's jailbreak functionality targets specific iOS versions, the underlying checkm8 exploit and pongoOS loading work regardless of the installed iOS version.

**palera1n** (successor for newer iOS):
- Supports iOS/iPadOS 15.0 through 18.7.4
- Uses checkra1n's 0.1337.x builds to boot into pongoOS
- Maintains its own PongoOS fork (last updated January 5, 2026)
- Supports A8 through A11 and T2 devices
- Active development through late 2025

**Relevance to iPad Air 2**: checkra1n/palera1n can load pongoOS on the iPad Air 2 regardless of iOS version installed. This is the first step in the boot chain.

**License**: checkra1n is proprietary (binary-only distribution). palera1n is open source (MIT).

Sources:
- https://checkra.in/
- https://checkra.in/releases/
- https://palera.in
- https://github.com/palera1n/palera1n
- https://theapplewiki.com/wiki/Palera1n

---

## 3. pongoOS — Pre-Boot Execution Environment

**Purpose**: Pre-boot execution environment for Apple devices, loaded via checkm8. Provides a shell, USB communication, module loading, and the ability to hand off to alternative operating systems (iOS/XNU or Linux).

**GitHub**: https://github.com/checkra1n/PongoOS
- 2,700 stars, 464 forks
- MIT License
- Latest tagged release: 2.6.1 (January 15, 2023)
- Active development on master branch (commits by Siguza through 2024-2025)
- palera1n maintains a separate fork with updates through January 2026

**Key capabilities**:
- Interactive shell accessible over USB
- Module loading system for extending functionality at runtime
- Kernel Patch Framework (KPF) for XNU kernel modification
- Linux kernel loading: accepts Image.lzma (compressed kernel), device tree blob, and initramfs
- SEP (Secure Enclave Processor) exploitation capabilities
- Runs at EL1 (kernel privilege level) on the application processor

**How it hands off to Linux**:
1. checkm8 exploit runs, loads pongoOS into device memory
2. pongoOS boots, initializes USB, presents shell via `pongoterm`
3. A loader script (e.g., `load_linux.py`) sends kernel image, device tree binary, and ramdisk to pongoOS over USB
4. pongoOS places these in memory at appropriate addresses
5. `bootx` command triggers handoff: sets up CPU state, passes device tree pointer, jumps to kernel entry point

**Build artifacts**:
- `Pongo` — Mach-O of main pongoOS
- `Pongo.bin` — bare metal binary
- `checkra1n-kpf-pongo` — kernel patchfinder module
- `PongoConsolidated.bin` — pongoOS + KPF merged

**Build requirements**: macOS (Xcode) or Linux (clang, ld64, cctools).

**Relevance to iPad Air 2**: pongoOS supports all checkm8 devices including A8X. It is the critical bridge between the checkm8 exploit and Linux kernel boot. The module system allows loading device-specific drivers/configurations.

Sources:
- https://github.com/checkra1n/PongoOS
- https://deepwiki.com/checkra1n/PongoOS
- https://github.com/palera1n/PongoOS
- https://github.com/hmk3r/iphone-5s-linux-howto

---

## 4. Project Sandcastle — Android/Linux on iPhone

**Purpose**: Proof-of-concept demonstrating Android and Linux running on iPhone hardware. Created by Corellium.

**Released**: March 6, 2020.

**What it achieved**:
- Booted Android 10 (AOSP) and Linux on iPhone 7/7+ and iPod Touch 7th gen
- Used checkm8 exploit via pongoOS for boot chain
- Built custom kernel (linux-sandcastle, forked from Linux stable)
- Created device trees for Apple A10 (T8010) SoC
- Implemented Apple Interrupt Controller (AIC) driver from scratch
- Built FIQ (Fast Interrupt Request) support for AArch64 Linux (previously unsupported)
- Custom touchscreen daemon (hx-touchd) for iPhone touch controller

**Hardware support status (iPhone 7)**:

| Feature | Status |
|---------|--------|
| CPU | Working |
| UART | Working |
| USB | Working |
| AIC (interrupt controller) | Working |
| Display | Working |
| I2C, SPI | Working |
| NAND storage | Working |
| Multitouch | Working |
| PMU (power management) | Working |
| WLAN (WiFi) | Working |
| Bluetooth | Working |
| GPU | Not working |
| Camera | Not working |
| Audio | Not working |
| Cellular | Not working |

**Current status (2026)**: Effectively abandoned. No commits to GitHub repository since March 8, 2020 (two days after initial release). The project website (projectsandcastle.org) remains online but has not been updated.

**Key technical contributions**:
- `corellium/linux-sandcastle` — kernel fork with Apple SoC support (199 stars, 52 forks)
- AIC interrupt controller driver (later adapted and upstreamed by Asahi Linux for M1)
- FIQ support for AArch64 Linux (novel contribution, this path was unused in standard ARM64 Linux)
- Device tree definitions for A10 SoC peripherals
- Buildroot-based rootfs generation

**Relevance to iPad Air 2**: Sandcastle targeted A10 (iPhone 7), not A8X. However:
- The AIC driver is relevant: A8X uses the same interrupt controller family
- FIQ handling code is directly reusable
- The boot chain approach (checkm8 -> pongoOS -> Linux) is identical
- Kernel patches for Apple-specific peripherals (UART, I2C, SPI) may transfer
- Device tree structure provides a template, though peripheral addresses differ

**License**: GPL v2 (kernel), MIT (supporting tools).

Sources:
- https://github.com/corellium/projectsandcastle
- https://projectsandcastle.org/status
- https://projectsandcastle.org/history
- https://github.com/corellium/linux-sandcastle

---

## 5. postmarketOS — iPhone/iPad Support

**Purpose**: Alpine Linux-based mobile OS targeting long-term support for smartphones. Supports approximately 723 device models as of 2026.

**Apple device support**:

### iPhone 7/7+ (apple-iphone7)
- **Status**: Testing category
- **Kernel**: 5.4.12 (mainline)
- **Architecture**: aarch64
- **Boot method**: DFU mode via checkra1n/pongoOS (requires PC + USB each boot)
- **Working**: USB networking, battery (charging + level), display, touchscreen, WiFi, Bluetooth, internal storage (APFS)
- **Not working/untested**: GPU/3D acceleration, audio, camera, cellular, GPS, accelerometer
- **Known issues**: Screen color abnormalities, no standalone boot without PC

### iPhone 8 (apple-d20)
- **Status**: Needs testing, mainline fork available but not yet ported

### iPhone SE 1st gen (apple-n69)
- **Status**: Wiki page exists, minimal information

### iPhone X
- **Status**: Port announced in late 2025, early development

### iPad devices
- **Status**: A device category page exists for "Apple iPad 1G" but no active iPad ports confirmed in postmarketOS pmaports repository

**Relevance to iPad Air 2**: No direct iPad Air 2 port exists. However:
- The iPhone 7 port demonstrates the postmarketOS build system works with Apple hardware
- The checkra1n/pongoOS boot chain integration is already implemented
- The Alpine Linux base and packaging system work on aarch64
- Adapting the iPhone 7 port to iPad Air 2 would require: new device tree, display driver adjustments, and A8X-specific kernel configuration

Sources:
- https://wiki.postmarketos.org/wiki/Device:iPhone_7/7+
- https://wiki.postmarketos.org/wiki/Apple_iPhone_8_(apple-iphone10,1)
- https://gitlab.com/postmarketOS/pmaports/-/merge_requests/2289
- https://tuxphones.com/iphone-7-now-boots-postmarketos-linux/

---

## 6. Asahi Linux — Apple Silicon Macs

**Purpose**: Port Linux to Apple Silicon Macs (M1, M2, M3, M4 chips). Led by Hector Martin (marcan).

**Current status (2026)**:
- Mature project with Fedora Asahi Remix as primary distribution
- OpenGL 4.6, OpenGL ES 3.2, Vulkan support via Mesa AGX driver
- GPU driver uAPI merged into mainline Linux kernel
- Mesa driver fully upstreamed (Mesa 25.2+, fork retired)
- Supports M1, M2, M3 families across MacBook, iMac, Mac Mini, Mac Studio, Mac Pro

**Significant setback**: Asahi Lina paused all Apple GPU kernel DRM driver development indefinitely (March 2025). The kernel-side DRM driver is not yet upstreamed and still targets only M1/M2 generations.

**Relevance to older A-series chips (A8X)**:

Asahi Linux explicitly states that iPhones and iPads are NOT supported and are not a project goal. The project FAQ notes that even with code execution, booting a custom kernel on iOS devices requires different approaches than on Macs.

However, several shared elements exist:

| Component | Shared? | Notes |
|-----------|---------|-------|
| Apple Interrupt Controller (AIC) | Yes | AIC driver upstreamed in Linux 5.13, same controller family on A8X |
| Boot approach | Partially | m1n1 bootloader concepts similar to pongoOS role |
| Device tree methodology | Yes | Apple DT -> Linux DT conversion techniques applicable |
| CPU bring-up | Partially | ARM64 EL2/EL1 transition patterns similar |
| GPU driver (AGX) | No | M-series AGX GPU is architecturally different from A8X's PowerVR GXA6850 |
| DART (IOMMU) | Partially | Similar IOMMU design across Apple SoCs |
| Mailbox/IPC | Partially | Apple mailbox controller patterns shared |

**AGX vs PowerVR**: The M-series GPU (AGX) has PowerVR heritage but is largely bespoke. Asahi's Mesa driver does not apply to older PowerVR GPUs. The PowerVR GXA6850 in the A8X requires the separate Imagination PowerVR Mesa driver (see Section 9).

Sources:
- https://asahilinux.org/
- https://asahilinux.org/docs/hw/soc/agx/
- https://asahilinux.org/2025/10/progress-report-6-17/
- https://www.phoronix.com/news/Asahi-Lina-Steps-Down-Linux-GPU
- https://www.phoronix.com/news/Mesa-AGX-More-PVR-Reference

---

## 7. Linux-on-iPhone/iPad GitHub Projects

### 7a. Konrad Dybcio — Mainline Linux on A7/A8/A8X (2022)

**Achievement**: Booted mainline Linux kernel 5.18 on iPad Air 2 and other A7/A8/A8X devices in June 2022. This is the single most relevant prior work for this project.

**Supported devices**: iPhone 5S, iPhone 6/6+, iPod Touch 6th gen, iPad Air 1, **iPad Air 2**, iPad Mini 2/3/4.

**Technical details**:
- Used checkm8 -> pongoOS -> Linux boot chain
- Based on Sandcastle project research but solved critical MMU enablement independently
- Kernel branch: apple/v5.19-rc1
- Framebuffer working (basic display output)
- Basic peripheral bring-up achieved
- Built using postmarketOS distribution

**GitHub**: https://github.com/konradybcio (also maintains a pongoOS fork at https://github.com/konradybcio/pongoOS)

**Current status**: Development appears intermittent ("revisit every now and then" approach). No major updates found post-2022, but the kernel patches exist and provide a direct starting point for iPad Air 2.

### 7b. hmk3r/iphone-5s-linux-howto

**Purpose**: Step-by-step guide for booting Linux on iPhone 5S via pongoOS.

**GitHub**: https://github.com/hmk3r/iphone-5s-linux-howto

**What it documents**:
1. Enter DFU mode, run checkra1n with pongoOS binary
2. Use `load_linux.py` to send kernel (Image.lzma), device tree, and ramdisk over USB
3. Boot into postmarketOS

**Relevance**: Demonstrates the complete boot procedure applicable to all checkm8 devices. Process is directly transferable to iPad Air 2 with appropriate kernel/DT.

### 7c. planetbeing/iphonelinux (historical)

**Purpose**: Original Linux port for iPhone 2G/3G (2008-2010). 587 stars.

**Status**: Completely inactive since ~2010. Targeted 32-bit ARMv6 (Samsung S5L8900), not relevant to ARM64 A8X.

**Historical significance**: First demonstration that Linux could run on iPhone hardware. Created xpwn (NOR firmware loader) and libdmg-hfsplus.

### 7d. Hoolock Linux

**Purpose**: Bring Linux to Apple iPhone, iPad, iPod Touch, Apple TV, and iBridge devices with A7-A11/T2 SoCs.

**GitHub**: https://github.com/HoolockLinux

**Status**: Active project with documentation and tutorials. Acknowledges Asahi Linux for shared techniques. Maintains m1n1 bootloader adaptation and docs.

**Relevance**: Directly targets the same device family as this project. Documentation on iBoot setup and boot chain may be useful.

### 7e. ipadlinux.org

**Purpose**: Tracking site created in 2019 to aggregate all efforts to bring Linux to iPad hardware.

**Status**: Informational site, not an active development project.

Sources:
- https://hackaday.com/2022/06/12/boot-mainline-linux-on-apple-a7-a8-and-a8x-devices/
- https://github.com/hmk3r/iphone-5s-linux-howto
- https://github.com/planetbeing/iphonelinux
- https://github.com/HoolockLinux
- https://ipadlinux.org/
- https://en.wikipedia.org/wiki/Linux_on_Apple_devices

---

### 7f. Project Cascadia — Mainline Linux on 32-bit A5 (and A6X groundwork)

**Repo**: https://github.com/rzxvx/Project-Cascadia (created 2026-08, active as of
2026-11-04, ~650 commits). Not related to this repository's boot chain: ARMv7, no pongoOS.

- iPad mini 1 (A5): Linux 6.12, both cores, touch, Wi-Fi, Bluetooth, audio, SGX543 GPU
  with OpenGL ES 2.0, XFCE desktop. iPad 2 (A5): RAM-only USB shell.
- Boot chain: checkm8 (Raspberry Pi Pico, since A5 needs it) or kDFU from jailbroken iOS,
  patched iBSS and iBEC from the 8.4.1 IPSW, staging loader built on teutekeune's
  iBSSloader, `zImage-dtb` at 0x80008000, embedded Alpine initramfs. Tethered.
- A6X (iPad 4): declared next target (issue #6, 2026-10-10). PR #7 merged a p102ap DTS
  translated from the Apple Device Tree and A6X support in `adt_to_dts.py`. No kernel
  bring-up yet. Hardware map in `research/compatibility-matrix.md`, Generation 2.
- Also hosts A12 (iPhone XR, contributed) and A13 (iPhone 11) trees via m1n1, which
  overlap HoolockLinux's territory.

**Relevance to iPad Air 2**: none for the boot chain. Relevant as the only live ARMv7
effort for the 13 32-bit iPad variants, and for its Z2 touch and BCM4334 HSIC work.

### 7g. a6-handheld-linux — Linux on iPhone 5 (A6)

**Repo**: https://github.com/landrucode/a6-handheld-linux (2026-10-15, single commit).
iPhone5,2 (N42AP) only. Works: both cores, software-rendered display, touch, audio,
Wi-Fi (brcmfmac over HSIC), USB networking, charging policy; desktop on labwc. No GPU,
no backlight, no Bluetooth. Boot: checkm8 (any tool), NyanSatan's checkm8_bootkit loads
iOS 8.4.1 iBSS and iBEC, then a Linux kernel in A6 kernelcache format with the device
tree attached. Kernel sources in-repo (mainline at a pinned commit). Author states it has
not been rebuilt from a fresh checkout. Closest existing sibling to an iPad 4 port: same
Swift cores and iBoot generation; display (CLCD plus eDP) and GPU (SGX554MP4) differ.

## 8. Corellium — Commercial iOS Virtualization

**Purpose**: Commercial platform providing full iOS device virtualization for security research, app testing, and forensics.

**Technology**: CHARM (Corellium Hypervisor for ARM) - proprietary type-1 hypervisor running on native ARM hardware. Virtualizes complete Apple devices including SoC, peripherals, and chipsets.

**Capabilities**:
- Spins up jailbroken or non-jailbroken iOS devices on demand
- Root access without relying on iOS vulnerabilities (built into the hypervisor)
- Supports latest iOS versions (iOS 26 as of 2026) and latest hardware (iPhone 17)
- Memory Integrity Enforcement (MIE) research support

**Open-source contributions**:
1. **Project Sandcastle** (see Section 4): Linux kernel, device trees, boot tools for iPhone 7
2. **linux-sandcastle kernel**: GPL v2 kernel fork with Apple SoC support
3. **linux-m1**: Early Linux kernel port for Apple M1 (preceded Asahi Linux's effort)
4. **AIC driver**: Apple Interrupt Controller implementation (later adapted for upstream Linux)
5. **Device tree bindings**: Published DT bindings for Apple SoC peripherals
6. Financial contributions to open-source projects via Open Collective

**Published research relevant to hardware documentation**:
- Detailed Apple SoC peripheral documentation derived from virtualization work
- AIC interrupt controller behavior and register definitions
- FIQ handling on AArch64 for Apple platforms
- A10 SoC memory map and peripheral address layout
- Blog post: "How we ported Linux to the M1" (detailed technical methodology)

**Relevance to iPad Air 2**: Corellium's kernel patches, AIC driver, and device tree work provide the most complete reference for Apple SoC peripheral programming. Their virtualization platform could theoretically be used for development without physical hardware, though it is a paid commercial product (pricing not public, primarily enterprise/government customers).

**License**: Project Sandcastle tools are MIT, kernel work is GPL v2, the CHARM hypervisor is proprietary.

Sources:
- https://www.corellium.com
- https://www.corellium.com/blog/linux-m1
- https://github.com/corellium/projectsandcastle
- https://github.com/corellium/linux-sandcastle
- https://github.com/corellium/linux-m1

---

## 9. PowerVR GPU Driver Status (Supplementary)

The iPad Air 2 uses a PowerVR GXA6850 GPU (Imagination Technologies Rogue architecture). GPU acceleration is critical for a usable Linux desktop.

**Current Mesa driver status (2026)**:
- Imagination Technologies has an open-source Vulkan driver in Mesa (the "PVR" driver)
- Vulkan 1.0 conformant for Rogue architecture GPUs (Mesa 25.3)
- Vulkan 1.2 conformance validation planned for 2026
- Series 6XE, 6XT, 8XE, and B-Series GPUs have unofficial/experimental support in Mesa 25.3
- The GXA6850 is a Series 6XT GPU

**Limitations**:
- No OpenGL driver (Vulkan only)
- Support for older Series 6 GPUs is unofficial and not actively developed by Imagination
- Requires appropriate firmware binaries
- No guarantee of functionality on all Rogue GPUs
- Imagination has stated zero plans to officially support anything older than their latest GPUs

**Assessment**: The PowerVR GXA6850 has a theoretical path to GPU acceleration via the Mesa PVR Vulkan driver, but it is not a priority for Imagination and may require community effort to get working reliably. Software rendering (llvmpipe) is the likely fallback.

Sources:
- https://docs.mesa3d.org/drivers/powervr.html
- https://www.phoronix.com/news/PowerVR-Mesa-More-GPUs
- https://blog.imaginationtech.com/imagination-and-our-commitment-to-open-source
- https://developer.imaginationtech.com/solutions/open-source-gpu-driver/

---

## Summary: Reusability Matrix for iPad Air 2 (A8X)

| Project | Directly reusable | What to reuse |
|---------|-------------------|---------------|
| checkm8 | Yes | Exploit works on A8X, use gaster or ipwndfu |
| checkra1n/palera1n | Yes | pongoOS loading mechanism, palera1n supports iOS 15+ |
| pongoOS | Yes | Pre-boot environment, Linux loading, USB shell |
| Project Sandcastle | Partially | AIC driver, FIQ support, kernel structure, boot chain pattern |
| postmarketOS | Partially | Build system, rootfs generation, packaging; no iPad Air 2 port |
| Asahi Linux | Partially | Upstreamed AIC driver, DART/IOMMU, DT methodology |
| Konrad Dybcio's work | Yes | **Directly booted Linux on iPad Air 2**, kernel patches exist |
| Hoolock Linux | Partially | Documentation, A7-A11 targeting, boot tutorials |
| Corellium | Partially | Kernel patches, device trees, hardware documentation |
| PowerVR Mesa | Maybe | Experimental Vulkan driver for Rogue GPUs, Series 6XT |

## Key Findings

1. **Linux has already booted on iPad Air 2**: Konrad Dybcio demonstrated mainline Linux 5.18 running on iPad Air 2 in June 2022 with framebuffer and basic peripherals. This is the most important prior art.

2. **The boot chain is proven**: checkm8 -> pongoOS -> Linux is a well-established path used by multiple projects across A7-A11 devices.

3. **The boot is tethered**: Every boot requires a host computer with USB connection to re-run the checkm8 exploit. This is a permanent limitation of the checkm8 approach.

4. **Driver coverage is sparse**: Display framebuffer works, but GPU (PowerVR), audio, WiFi, Bluetooth, and cameras remain major gaps on A8X specifically. The iPhone 7 (A10) has better driver coverage thanks to Project Sandcastle.

5. **GPU is the largest open question**: The PowerVR GXA6850 has a theoretical path via Mesa PVR Vulkan driver, but official support is unlikely. Software rendering is the realistic near-term option.

6. **Active community is small but persistent**: palera1n (pongoOS fork) is actively maintained. Hoolock Linux targets the same device family. postmarketOS has infrastructure for Apple device ports.

7. **NixOS adds a new dimension**: No existing project uses NixOS as the userland. Cross-compilation for aarch64 is well-supported in Nix, and the declarative configuration model is well-suited to embedded/constrained hardware.
