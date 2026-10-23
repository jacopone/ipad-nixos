# Driver Gap Analysis: iPad Air 2 (A8X) Hardware

Per-subsystem analysis of iPad Air 2 hardware chips and their Linux driver status.
Research conducted February 2026. Storage section revised 2026-10-23.

## Summary Matrix

| Subsystem | Chip | Linux Driver | Status | Effort |
|-----------|------|-------------|--------|--------|
| Display | LG LP097QX2 (eDP) | simplefb / simpledrm | Working (basic) | Low |
| Touch | Broadcom BCM5976 | apple_z2 (adapt) | Documented (Z2 protocol) | Medium-High |
| WiFi | Broadcom BCM4354 (Murata module) | brcmfmac | Partial | Medium |
| GPU | PowerVR GXA6850 (Series 6XT) | pvr (Mesa) | Experimental | Very High |
| Audio | Cirrus Logic 338S1213 | None known | None | High |
| Battery/Power | Dialog 343S0675 PMIC + TI BQ27546 | None (proprietary) | None | High |
| USB | Synopsys DWC2 OTG | dwc2 | Likely working | Low-Medium |
| Bluetooth | Broadcom (in Murata module) | btbcm / hci_bcm | Partial | Medium |
| Sensors | Unknown (likely InvenSense/Bosch) | Unknown | Unknown | Medium |
| Storage/NAND | Apple ANS1 storage co-processor | asp (HoolockLinux `ans1` branch) | WIP, out of tree | High |

---

## 1. Display

### Hardware

- **Panel**: LG LP097QX2-SPAV
- **Resolution**: 2048 x 1536 (264 PPI), 9.7 inch IPS LCD
- **Interface**: eDP (embedded DisplayPort), not MIPI DSI
- **Display controller**: Integrated into the A8X SoC, Apple proprietary
- **Panel connector**: 42-pin eDP, 4 lanes

### Linux Driver Status

**Status: Working (basic framebuffer)**

The display works via `simplefb` (simple framebuffer) or `simpledrm` (DRM simple display
driver). This approach relies on iBoot (Apple's second-stage bootloader) having already
initialized the display pipeline before pongoOS takes over. The framebuffer memory address,
resolution, and pixel format are passed to Linux via the device tree.

What works:
- Static framebuffer output (console, basic GUI rendering)
- Resolution and color depth as configured by iBoot

What does not work:
- No dynamic display mode switching
- No power management (cannot turn display off/on programmatically)
- No hardware acceleration (compositing, overlays, scaling)
- Backlight control: device tree nodes for backlight are being added in Linux 6.15 patches

### Native DRM Driver

A proper DRM/KMS driver for the Apple display controller does not exist for A8X. Writing one
requires reverse engineering Apple's proprietary display pipeline, including:
- eDP PHY initialization
- Display timing controller registers
- Pixel pipeline configuration
- DRAM framebuffer allocation and scanout

Asahi Linux has done this work for M-series SoCs (the DCP driver), but the A8X display
controller predates the DCP architecture and uses a different register interface.

### Estimated Effort

Low for simplefb (already working). Very High for a native DRM driver.

### External Controller Option

Third-party eDP controller boards exist that can drive the LP097QX2 panel from HDMI input,
confirming the panel itself works with standard eDP signaling. This is relevant only for
hardware testing, not for in-situ Linux use.

Sources:
- https://hackaday.com/2019/07/18/put-those-ipad-displays-to-work-with-this-edp-adapter/
- https://www.phoronix.com/news/Apple-Silicon-DT-3-Linux-6.15
- https://www.kernel.org/doc/Documentation/devicetree/bindings/display/simple-framebuffer.txt

---

## 2. Touch

### Hardware

- **Controller**: Broadcom BCM5976 ("Cumulus")
- **Board designation**: U4100/U4150 (iPad Air 2)
- **Package**: 63-pin BGA
- **Interface**: SPI (to application processor)
- **Capabilities**: Multi-touch capacitive digitizer

The BCM5976 is used across iPhone 5 through 6 Plus, iPad Air 1/2, iPad Mini 1-4, and iPad
5th gen (2017). It is a proprietary Broadcom touch controller with no public datasheet.

### Linux Driver Status

**Status: None (direct), but the protocol is now documented via the Z2 driver in Linux 6.15**

No dedicated Linux driver exists for the BCM5976. However, the situation has improved
dramatically since the initial research:

- **apple_z2 kernel driver (Linux 6.15)**: Asahi Linux merged a driver for Apple's Z2
  touch protocol. Z2 is described as "the primary protocol for the touchscreen on mobile
  Apple devices." The finger data format in apple_z2 is structurally identical to the
  BCM5974 (USB MacBook) and applespi (SPI MacBook) drivers, confirming a protocol family
  spanning 2008-2024.
- **Project Sandcastle hx-touchd**: Corellium's userspace daemon for iPhone 7 uses Z2
  commands (0xE1-0xEE range) consistent with the apple_z2 driver's command set. The touch
  controller was described as "not very complex to interface with."
- **lemonjesus iPad touch project**: A Raspberry Pi Pico-based project that successfully
  drives an iPad 3 touchscreen by replaying captured Z2 initialization sequences. Confirms
  the Z2 protocol name and approach for older iPad models.

### Z2 Protocol Summary

- 16-byte command frames with 2-byte checksum
- Read interrupt command: 0xEB + counter + padding + checksum
- Control commands: 0xE1-0xEE (firmware upload, status, wake)
- Finger reports: 32 bytes per finger with abs_x/y, rel_x/y, tool_major/minor,
  orientation, touch_major/minor, pressure (identical to BCM5974 format)
- SPI max frequency: ~11.5 MHz
- Firmware: Z2FW container format, uploaded during initialization
- Calibration: per-device blob, loaded during firmware upload

See research/touch-re.md for complete protocol documentation.

### Path to Working

1. **Analyze IPSW firmware** — extract AppleMultitouchSPI.kext and multitouch firmware from
   iPad Air 2 IPSW using ipsw tool + Ghidra with ghidra_kernelcache framework
2. **Verify protocol** — use lemonjesus Pico approach to capture and replay Z2 init sequence
3. **Write A8X SPI driver** — Samsung-derived SPI controller (not the M-series apple,spi);
   Corellium wrote one for A10 in linux-sandcastle
4. **Adapt apple_z2 driver** — add iPad Air 2 device tree bindings, BCM5976-specific quirks
5. **Extract firmware from IPSW** — adapt Asahi Linux multitouch.py extraction pipeline

### Estimated Effort

Medium-High (reduced from High). The Z2 protocol is now documented through three independent
sources (apple_z2 kernel driver, hx-touchd, lemonjesus project). The remaining work is
A8X SPI controller bring-up and BCM5976-specific adaptation.

Sources:
- https://patchwork.kernel.org/project/linux-arm-kernel/patch/20241128-z2-v2-2-76cc59bbf117@gmail.com/
- https://github.com/corellium/projectsandcastle/tree/master/hx-touchd
- https://github.com/lemonjesus/ipad-touch-screen
- https://github.com/AsahiLinux/asahi-installer/blob/main/asahi_firmware/multitouch.py
- https://github.com/torvalds/linux/blob/master/drivers/input/mouse/bcm5974.c

---

## 3. WiFi

### Hardware

- **Module**: Murata 339S02541
- **Chipset**: Broadcom BCM4354 (802.11ac, 2x2 MIMO)
- **Interface**: SDIO (to application processor)
- **Bands**: 2.4 GHz and 5 GHz
- **Bluetooth**: Integrated (combo WiFi+BT module)

The Murata module is a shielded package containing the Broadcom BCM4354 SoC, which handles
both WiFi and Bluetooth. The WiFi portion connects via SDIO, the Bluetooth portion via UART.

### Linux Driver Status

**Status: Partial (driver exists, firmware is the blocker)**

The `brcmfmac` driver in the Linux kernel supports the BCM4354 chipset. The driver was
introduced in kernel 2.6.39 and has been continuously maintained.

What exists:
- `brcmfmac` kernel module: supports BCM4354 over SDIO
- Basic driver infrastructure for initialization, scanning, association

What is missing:
- **Firmware**: The BCM4354 requires proprietary firmware blobs to operate. The specific
  firmware variant for Apple's Murata module is not in the linux-firmware repository.
  Apple-specific firmware files must be extracted from iOS.
- **NVRAM**: Each BCM4354 variant requires a board-specific NVRAM configuration file that
  specifies antenna configuration, regulatory domain, and calibration data. The Apple NVRAM
  format may differ from standard Broadcom NVRAM.
- **CLM blob**: Country Locale Map blob that defines regulatory limits. Tightly linked to each
  model variant, making generic distribution impractical.

### Reference: iPhone 7 WiFi

Project Sandcastle and postmarketOS both achieved working WiFi on iPhone 7 (which uses a
different Broadcom chip, BCM4355). The approach:
1. Extract firmware from iOS IPSW
2. Convert firmware to brcmfmac format
3. Create appropriate NVRAM file
4. Place files in `/lib/firmware/brcm/`

The same approach should work for iPad Air 2 with BCM4354-specific firmware.

### Path to Working

1. Extract BCM4354 firmware from iPad Air 2 iOS firmware (IPSW)
2. Identify the SDIO bus configuration in the A8X device tree
3. Create the NVRAM configuration file for the Murata 339S02541 module
4. Test with brcmfmac driver, debug any Apple-specific initialization quirks
5. brcmfmac patches for Apple T2 and M1 platforms exist upstream and may contain relevant
   Apple-specific code paths

### Estimated Effort

Medium. The driver exists and the chip is supported. The main work is firmware extraction
and NVRAM configuration. Prior art from iPhone 7 and Apple T2 Mac Linux work demonstrates
the process.

Sources:
- https://wireless.wiki.kernel.org/en/users/drivers/brcm80211
- https://wiki.debian.org/brcmfmac
- https://lwn.net/Articles/879910/
- https://www.spinics.net/lists/linux-wireless/msg231113.html

---

## 4. GPU

### Hardware

- **GPU**: Imagination Technologies PowerVR GXA6850
- **Architecture**: Rogue, Series 6XT
- **Configuration**: 8 clusters (two GX6450 halves), Apple-customized ("A" suffix)
- **Shader cores**: 8 USC (Unified Shading Clusters)
- **API support (iOS)**: OpenGL ES 3.0, Metal
- **Manufacturing**: TSMC 20nm (integrated in A8X SoC)

The "GXA6850" designation indicates Apple customization of the standard Imagination GX6450
design, doubled to 8 clusters. This is the most powerful mobile GPU from late 2014.

### Linux Driver Status

**Status: Experimental (Mesa PVR driver exists for Rogue, GXA6850 not listed as supported)**

Imagination Technologies has released an open-source Vulkan driver for PowerVR Rogue GPUs
in Mesa. As of Mesa 25.3:

**Actively supported GPUs:**
- AXE-1-16M (A-Series)
- BXM-4-64 (B-Series)
- BXS-4-64 (B-Series) -- Vulkan 1.0 conformant

**Partially supported:**
- GX6250 (Series 6XT) -- various core-specific features unimplemented, instability expected

**Unsupported (listed):**
- GX6650 (Series 6XT)
- Various Series 7XE, 8XE, B-Series variants

**Not listed at all:**
- GXA6850 -- Apple's custom variant is not mentioned in Mesa documentation

The Mesa PVR Vulkan driver requires the environment variable
`PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1` for non-conformant GPUs.

### Kernel DRM Driver

The PowerVR kernel-space DRM driver was merged in Linux 6.8. It provides:
- GEM buffer management
- Job submission
- Power management for PowerVR GPUs

However, the kernel driver targets specific SoC integrations. Apple's integration of the
PowerVR GPU into the A8X is not supported by the upstream kernel driver, which targets
platforms like MediaTek MT8173 and Texas Instruments AM62x.

### Assessment

The GXA6850 has three fundamental problems for Linux GPU acceleration:

1. **Apple customization**: The "A" in GXA6850 means Apple made modifications to the standard
   Imagination design. Register offsets, clock gating, power islands, or firmware interfaces
   may differ from the reference design.

2. **No kernel DRM support for Apple SoC**: The PowerVR kernel driver does not include an
   Apple platform backend. Writing one requires reverse engineering the A8X's GPU MMIO
   interface, power management, and memory management (IOMMU/DART) integration.

3. **Mesa driver immaturity for Series 6XT**: Even the GX6250 (the most similar supported
   GPU) is only partially supported with expected instability.

### Realistic Expectations

- **Software rendering (llvmpipe)**: The realistic near-term option. Mesa's llvmpipe provides
  OpenGL via CPU rendering. Performance will be limited but functional for basic desktop use.
- **Vulkan via Mesa PVR**: Theoretically possible but requires kernel DRM driver work for the
  Apple A8X platform, plus Mesa PVR driver support for the GXA6850 variant. This is a large
  undertaking.
- **Proprietary blob**: Imagination previously provided binary-only GPU drivers for some
  platforms. No such driver exists for the A8X Linux combination.

### Estimated Effort

Very High. GPU acceleration on iPad Air 2 Linux is the single hardest driver challenge.
Software rendering is the pragmatic path. Hardware acceleration would require months of
reverse engineering and driver development.

Sources:
- https://docs.mesa3d.org/drivers/powervr.html
- https://www.notebookcheck.net/Imagination-PowerVR-GXA6850.128993.0.html
- https://en.wikipedia.org/wiki/Apple_A8X
- https://blog.imaginationtech.com/the-complete-guide-to-powervr-rogue-gpus-specifications-features-api-support/
- https://www.phoronix.com/news/PowerVR-Mesa-More-GPUs

---

## 5. Audio

### Hardware

- **Audio codec**: Cirrus Logic 338S1213
- **Amplifier**: Maxim Integrated MAX98721BEWV (boosted class amplifier)
- **Interface**: Likely I2S (audio data) + I2C/SPI (control)
- **Speakers**: Stereo (dual speaker design in iPad Air 2)

The 338S1213 is an Apple part number for a Cirrus Logic audio codec. Apple has used Cirrus
Logic codecs across its entire product line for over a decade. The exact Cirrus Logic public
model number corresponding to 338S1213 is not publicly documented.

### Linux Driver Status

**Status: None**

No Linux driver exists for the 338S1213 audio codec. Key issues:

- The internal Cirrus Logic model number is unknown, making it impossible to map to existing
  ALSA/ASoC codec drivers
- Apple uses proprietary register configurations for their Cirrus Logic codecs
- Cirrus Logic has upstreamed Linux drivers for some of their codecs (CS42L42, CS42L51,
  CS35L56, etc.), but the specific codec in iPad Air 2 is not covered
- The audio path on Apple SoCs uses a custom audio DMA engine, not a standard I2S controller
- On Apple Silicon Macs, Asahi Linux has done extensive work on Cirrus Logic codec drivers
  (CS42L83, CS42L84), but these are newer chips with different register sets

### Path to Working

1. Identify the Cirrus Logic public model number for 338S1213 (possibly through iOS firmware
   analysis or die photography)
2. Reverse engineer the A8X audio DMA controller interface
3. Write an ASoC machine driver that ties together: CPU DAI (A8X audio controller), codec
   driver (338S1213), and platform DMA
4. This is a three-layer driver stack with no existing components for the A8X

### Estimated Effort

High. Requires reverse engineering both the audio codec register set and the A8X audio DMA
engine. No prior work exists for A8X audio specifically.

Sources:
- https://www.ifixit.com/Teardown/iPad+Air+2+Teardown/30592
- https://www.eeherald.com/section/news/onws20141102003.html
- https://github.com/CirrusLogic/linux-drivers

---

## 6. Battery and Power Management

### Hardware

- **PMIC**: Apple 343S0675 (Dialog Semiconductor origin, U8100 board designation)
  - WiFi model: 343S0675
  - Cellular model: 343S0674
- **Fuel gauge**: Texas Instruments BQ27546-G1 (single-cell Li-Ion battery gauge)
- **Charging IC**: CBTL1610A2 "Tristar" (USB charging/identification IC)
- **Battery**: 7340 mAh, 3.76V, single cell Li-polymer

Apple acquired Dialog Semiconductor's PMIC division in 2018 ($600M deal), transferring 300+
employees and the technology to Apple. The 343S0675 is a Dialog-designed chip with Apple
part numbering.

### Linux Driver Status

**Status: None (PMIC), Partial potential (fuel gauge)**

**PMIC (343S0675):**
No Linux driver exists. The Dialog DA9xxx series has Linux kernel support (DA9052, DA9062,
DA9063), but the Apple 343S0675 is a custom variant with unknown register compatibility.
Without PMIC driver support:
- No voltage regulation control
- No power rail management
- No thermal management
- The device relies on iBoot's PMIC initialization (which persists until power cycle)

**Fuel gauge (BQ27546-G1):**
Texas Instruments fuel gauge drivers exist in the Linux kernel (`bq27xxx_battery` driver
family). The BQ27546 is a standard TI part with a public datasheet. It communicates over
I2C (or HDQ single-wire protocol). If the I2C bus is accessible from Linux, this chip
could potentially report battery level and health.

**Charging IC (Tristar CBTL1610A2):**
The Tristar chip handles USB identification and charging negotiation. No Linux driver exists.
Without it, the device cannot negotiate charging current with USB power sources. However,
basic USB power delivery (500mA from USB 2.0) may work without Tristar driver support.

### Estimated Effort

High for PMIC (custom chip, no documentation). Low-Medium for fuel gauge (standard TI part
with existing driver, if I2C bus is accessible). Medium for Tristar (would need reverse
engineering).

Sources:
- https://microsolderingsupply.com/index.php?route=product/product&product_id=271
- https://www.ti.com/product/BQ27546-G1
- https://eepower.com/news/apple-acquires-pmic-technology-and-employees-from-dialog-semi/

---

## 7. USB

### Hardware

- **Controller**: Synopsys DesignWare DWC2 OTG (USB 2.0)
- **External connector**: Lightning (proprietary)
- **Capabilities**: USB 2.0 High-Speed (480 Mbps), OTG (host + device modes)
- **Authentication**: Lightning connector includes an authentication chip

The Synopsys DWC2 OTG controller is used across all Apple SoCs from A-series through at
least A11. It was identified through iOS BootROM reverse engineering (the BootROM's USB
stack interfaces with the DWC2 registers directly).

### Linux Driver Status

**Status: Likely working (DWC2 driver exists, Apple platform glue needed)**

The Linux kernel has a well-maintained `dwc2` driver (`drivers/usb/dwc2/`). Corellium's
M1 Linux kernel fork included Synopsys DWC3 controller support for Apple platforms, and the
DWC2 is the USB 2.0 predecessor with similar register conventions.

What exists:
- `CONFIG_USB_DWC2=y` kernel driver: comprehensive DWC2 OTG support
- Device mode (USB gadget): device presents itself as a USB device to host
- Host mode: device acts as a USB host (with Lightning-to-USB adapter)
- OTG role switching

What is needed:
- Platform-specific initialization for the A8X (clock enable, PHY configuration)
- Device tree integration (register addresses, interrupt mapping)
- Lightning authentication may be needed for certain accessories (but not for basic USB
  communication after checkm8 exploit)

Project Sandcastle confirmed USB working on iPhone 7 (A10), which uses the same DWC2
controller family. pongoOS itself uses the DWC2 controller for USB communication, confirming
hardware functionality.

### USB Gadget Mode (Important for iPad Linux)

USB gadget mode is critical for iPad Linux because it enables:
- USB Ethernet (RNDIS/ECM): network connectivity to host computer
- USB serial (CDC ACM): serial console over USB
- USB mass storage: expose ramdisk or block device to host

This is likely the primary network interface for initial bring-up, since WiFi requires
additional firmware work.

### Estimated Effort

Low-Medium. The driver exists and the hardware is known to work (pongoOS uses it). Main work
is platform glue and device tree integration.

Sources:
- https://docs.kernel.org/driver-api/usb/dwc3.html
- https://github.com/googleprojectzero/ktrw/blob/master/ktrw_gdb_stub/source/usb/synopsys_otg.c
- https://github.com/corellium/linux-m1/commit/a3ae5f475cac7022dd8d55d321ccd631cc1535b1

---

## 8. Bluetooth

### Hardware

- **Chip**: Broadcom BCM4354 (combo WiFi+BT in Murata 339S02541 module)
- **Interface**: UART (to application processor)
- **Bluetooth version**: 4.0 (with BLE support)

The Bluetooth controller is integrated into the same Broadcom chip as WiFi. It connects
to the application processor via a separate UART interface.

### Linux Driver Status

**Status: Partial (driver exists, firmware is the blocker)**

The Linux kernel's `btbcm` and `hci_uart` drivers support Broadcom Bluetooth chipsets.
For BCM4354-based Bluetooth:

What exists:
- `hci_bcm` UART driver in the Linux kernel
- `btbcm` firmware loading framework
- Bluetooth HCI protocol support

What is missing:
- **Firmware**: Proprietary Broadcom Bluetooth firmware must be extracted from iOS
- **UART configuration**: The specific UART port, baud rate, and flow control settings for
  the A8X Bluetooth path need to be identified
- **WiFi co-dependency**: Some Broadcom combo chips require WiFi firmware to be loaded
  before Bluetooth will initialize properly

### Reference

postmarketOS has Bluetooth working on iPhone 7 (different Broadcom chip, BCM4355). The
approach involves extracting firmware and configuring the UART interface.

### Estimated Effort

Medium. Similar to WiFi: the driver infrastructure exists, but firmware extraction and
platform-specific UART configuration are needed.

Sources:
- https://wiki.gentoo.org/wiki/Broadcom_Bluetooth
- https://github.com/winterheart/broadcom-bt-firmware

---

## 9. Sensors

### Hardware

The iPad Air 2 contains several sensors, though exact chip models are not fully documented
in public teardowns:

- **Accelerometer + Gyroscope**: Likely an InvenSense or Bosch 6-axis IMU
  - Apple M8 motion coprocessor (NXP LPC18B1UK) aggregates sensor data
  - The M8 communicates with the A8X over I2C or SPI
- **Ambient Light Sensor (ALS)**: Unknown vendor, likely on I2C
- **Barometer**: Unknown vendor
- **Magnetometer**: Unknown vendor (if present)
- **Touch ID**: Fingerprint sensor connected via SPI to the Secure Enclave (not accessible
  from application processor without SEP cooperation)

### Linux Driver Status

**Status: Unknown**

No specific driver work has been done for iPad Air 2 sensors. However:

- If the sensors are standard InvenSense (MPU-6xxx) or Bosch (BMI160, BMG160) parts, Linux
  IIO drivers exist for them
- The M8 motion coprocessor adds a layer of abstraction: the A8X may not talk to sensors
  directly, instead receiving processed data from the M8 via I2C/SPI
- If the M8 is in the path, a driver for the M8's protocol is needed (proprietary, no
  documentation)

### Path to Working

1. Identify exact sensor chips via die photography or iOS driver analysis
2. Determine whether the A8X communicates with sensors directly or via the M8 coprocessor
3. If direct: use existing IIO drivers for the identified chips
4. If via M8: reverse engineer the M8 communication protocol

### Estimated Effort

Medium. If sensors are accessible directly on I2C with standard chip IDs, existing drivers
may work with minimal effort. If the M8 coprocessor is in the path, effort increases
significantly.

Sources:
- https://www.ifixit.com/Teardown/iPad+Air+2+Teardown/30592
- https://www.eeherald.com/section/news/onws20141102003.html

---

## 10. Storage / NAND

### Hardware

- **NAND flash**: SK Hynix (16/64/128GB depending on model)
- **Controller**: ANS1 storage co-processor (ASP), an RTKit core with an AKF mailbox,
  integrated in the SoC (A7, A8, A8X)
- **Flash Translation Layer**: Apple proprietary (derived from Samsung Whimory FTL), runs in
  the ANS1 firmware
- **Encryption**: Hardware AES-256 encryption, UID-keyed, between NAND and DRAM
- **File system**: APFS (on iOS 10.3+) or HFS+ (older iOS)

### Linux Driver Status

**Status: WIP, out of tree (HoolockLinux `ans1` branch). Not integrated or tested here.**

HoolockLinux has a driver for the ANS1 storage processor (reported in issue #2), verified
2026-10-23:

- **Where**: branch [`ans1`](https://github.com/HoolockLinux/linux/tree/ans1) of
  HoolockLinux/linux, head `ed8528f482a5` (2026-09-03), all commits by Nick Chan. The branch
  is 27 commits ahead of the default `hoolock` branch and not merged into it.
- **Files**: `drivers/block/asp.c` (driver, "WIP: ANS1 driver", 3b237c39df79), Kconfig
  `APPLE_ASP` ("found on devices with Apple A7, A8, A8X SoCs"), binding
  `Documentation/devicetree/bindings/block/apple,s5l8960x-ans.yaml`
  (`apple,s5l8960x-ans`, `apple,t7000-ans`, `apple,t7001-ans`), plus RTKit protocol v10 and
  64-bit AKF mailbox support it depends on.
- **A8X**: the T7001 device tree nodes come from a commit titled
  "[WIP] arm64: dts: apple: t7001: Add ASP nodes" (32c5dac3841f); `t7001-air2.dtsi` enables
  the node for the iPad Air 2.
- **HoolockLinux status**: [features/A8.md](https://github.com/HoolockLinux/docs/blob/HEAD/features/A8.md)
  lists Internal Storage as WIP for A8 and A8X (docs commit 23ebe1fbc3, 2026-09-04,
  "update a7/a8 internal storage to WIP"). A7 is also WIP; A11 uses the NVMe driver
  upstream since Linux 6.18.

How the driver works, from `asp.c`:

- Linux talks to the ANS1 firmware over RTKit; the firmware implements the FTL, so Linux
  does not reimplement it. The firmware is loaded by earlier boot stages, and the device
  tree's `ans-firmware` reserved-memory region is "filled in by bootloader". In HoolockLinux
  that is m1n1; the pongoOS `bootl` path used by this repository does not fill it.
- I/O commands set `ASP_CMD_IO_FLAG_NO_ENCRYPTION`; per the driver's comment, without it the
  data is transformed in 128-bit blocks, "so likely encryption". Decrypting existing iOS data
  is not part of the driver.
- The user area is writable after a write-unlock command. Auxiliary namespaces (LLB, FW,
  NVRAM, SysCfg, ...) are exposed read-only because writing them can crash the controller
  persistently; SysCfg is described as "unrecoverable even with DFU".

Using it here requires the HoolockLinux kernel branch and the m1n1 boot path. Until then,
the background below still describes why this repository boots from RAM.

Apple's NAND storage subsystem is one of the most difficult components to support on Linux:

**The FTL problem:**
Apple uses a proprietary Flash Translation Layer originally based on Samsung's Whimory FTL
(reverse engineered by the openiBoot project for much older devices). The FTL has two layers:
- VFL (Virtual Flash Layer): remaps bad blocks, presents error-free view to upper layers
- FTL proper: translates logical block addresses to physical NAND pages

Modern Apple devices (A8X era) use an evolved version of this FTL. It is not NVMe or eMMC
compliant. The A8X has a custom NAND controller with a proprietary register interface.

**The encryption problem:**
A hardware AES-256 engine sits in the DMA path between NAND and DRAM. Every block is
encrypted with keys derived from the device's hardware-fused UID. Without the correct
keys (which are not readable, only usable through the AES engine), the NAND contents
are unreadable.

Even if a Linux NAND driver were written, the data on the NAND would be encrypted and
inaccessible without cooperation from the AES engine and knowledge of the key hierarchy.

**The practical solution so far: do not use internal NAND.**
Linux-on-iPhone/iPad setups have avoided the NAND:
- Boot from initramfs (everything in RAM)
- Use USB networking for file transfer
- Use NFS root over USB Ethernet
- On A11 devices, HoolockLinux supports internal storage through NVMe and ships
  partitioning tools; for A7/A8/A8X the ANS1 driver above is WIP

### Estimated Effort

High. A driver exists out of tree; the remaining work is the m1n1 boot path, a kernel
built from the HoolockLinux branch, and hardware testing. Existing iOS data stays
out of reach, and writes to the auxiliary namespaces can brick the device. Until the driver
is usable here:
1. Boot entirely from ramdisk (initramfs)
2. Use USB Ethernet for network storage

Sources:
- https://github.com/HoolockLinux/linux/tree/ans1 (head ed8528f482a5, 2026-09-03)
- https://github.com/HoolockLinux/linux/blob/ans1/drivers/block/asp.c
- https://github.com/HoolockLinux/docs/blob/HEAD/features/A8.md
- https://www.theiphonewiki.com/wiki/NAND
- https://news.ycombinator.com/item?id=12979195
- http://esec-lab.sogeti.com/posts/2012/06/28/low-level-ios-forensics.html

---

## Overall Assessment

### What Works Today (with existing code)

| Subsystem | Status | Notes |
|-----------|--------|-------|
| CPU (3x Typhoon cores) | Working | Mainline kernel supports A8X via device tree |
| UART/serial | Working | Samsung S3C-compatible, mainline driver |
| AIC (interrupt controller) | Working | Upstreamed driver (from Asahi Linux) |
| GPIO/pinctrl | Working | Upstreamed driver |
| Watchdog | Working | Upstreamed driver |
| Display (framebuffer) | Working | simplefb, depends on iBoot initialization |
| USB (basic) | Likely working | DWC2 driver exists, needs platform glue |

### What Could Work with Moderate Effort

| Subsystem | Status | Notes |
|-----------|--------|-------|
| WiFi | Needs firmware | brcmfmac driver exists, extract firmware from iOS |
| Bluetooth | Needs firmware | hci_bcm driver exists, extract firmware from iOS |
| Battery level | Needs testing | TI BQ27546 has Linux driver, if I2C accessible |
| USB gadget | Needs testing | DWC2 gadget mode for USB networking |

### What Requires Significant Reverse Engineering

| Subsystem | Status | Notes |
|-----------|--------|-------|
| Touch | Z2 protocol documented | Adapt apple_z2 driver + A8X SPI controller |
| Audio | No driver | Unknown Cirrus Logic codec, custom audio DMA |
| PMIC | No driver | Custom Dialog chip 343S0675 |
| Sensors | Unknown | May work if directly on I2C, problematic if via M8 |

### What Is Effectively Blocked

| Subsystem | Status | Notes |
|-----------|--------|-------|
| GPU acceleration | Experimental at best | PowerVR GXA6850 not supported in Mesa PVR |
| Internal NAND storage | Proprietary + encrypted | Use ramdisk/NFS instead |
| Camera | No driver | Not investigated, low priority for workstation use |
| Cellular (LTE model) | No driver | Not investigated, low priority |
| Touch ID | SEP-locked | Requires SEP cooperation, not feasible |

### Recommended Priority Order

For a functional Linux workstation on iPad Air 2:

1. **Boot chain** (checkm8 -> pongoOS -> kernel): Proven to work
2. **Display** (simplefb): Already functional
3. **USB gadget networking**: First network interface, enables SSH/NFS
4. **WiFi**: Broadcom driver exists, needs firmware extraction
5. **Touch**: Required for standalone use, needs reverse engineering
6. **Bluetooth**: Similar to WiFi, firmware extraction
7. **Audio**: Nice to have, significant RE needed
8. **Battery monitoring**: Quality of life, TI chip may be accessible
9. **GPU**: Long-term goal, software rendering in the meantime

Sources:
- https://www.ifixit.com/Teardown/iPad+Air+2+Teardown/30592
- https://www.eeherald.com/section/news/onws20141102003.html
- https://electronics360.globalspec.com/article/4690/teardown-apple-ipad-air-2
- https://projectsandcastle.org/status
- https://github.com/asdfugil/linux-apple-resources
- https://hackaday.com/2022/06/12/boot-mainline-linux-on-apple-a7-a8-and-a8x-devices/
