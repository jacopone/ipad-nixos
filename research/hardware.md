# iPad Air 2 (A8X) Hardware Mapping

Detailed hardware identification for the iPad Air 2, targeting Linux bringup.
Model numbers: A1566 (Wi-Fi), A1567 (Wi-Fi + Cellular).
Apple internal identifiers: iPad5,3 (j81, Wi-Fi) and iPad5,4 (j82, Cellular).

## 1. Apple A8X SoC (APL1012 / T7001 "Capri")

### CPU

- **Microarchitecture**: Apple Typhoon (2nd-generation Apple-designed ARMv8-A core)
- **Cores**: 3 (tri-core; up from dual-core Typhoon in A8)
- **Clock speed**: 1.5 GHz
- **ISA**: ARMv8-A (AArch64), 64-bit
- **Pipeline**: Out-of-order execution, enhanced branch prediction over Cyclone (A7)
- **Cache hierarchy**:
  - L1: 64 KB instruction + 64 KB data per core
  - L2: 2 MB shared across all 3 cores (doubled from 1 MB in A8)
  - L3: 4 MB shared across entire SoC (CPU + GPU)

### GPU

- **Architecture**: Imagination Technologies PowerVR Series 6XT (Rogue)
- **Configuration**: 8-cluster semi-custom design (Apple-modified)
- **Designation**: GXA6850 ("A" denotes Apple customization)
- **ALUs**: 256 FP32 (32 per cluster)
- **Note**: Imagination's largest official Series 6XT design is 6 clusters (GX6650). Apple created a custom 8-cluster variant. This is derived from the GX6450 (4-cluster) design in the A8, doubled.
- **API support** (iOS): OpenGL ES 3.0, Metal

### Memory Controller

- **Bus width**: 128-bit (doubled from 64-bit in A8)
- **Memory type**: LPDDR3
- **Bandwidth**: 25.6 GB/s
- **RAM chips**: 2x Elpida (Micron) F8164A3MD, 1 GB each = 2 GB total
- **Package**: Package-on-Package (PoP), RAM stacked on both sides of the SoC die

### Fabrication

- **Foundry**: TSMC
- **Process**: 20 nm HKMG (High-K Metal Gate)
- **Die size**: 128 mm^2
- **Transistor count**: ~3 billion

### Secure Enclave

- Integrated into the A8X die
- Handles Touch ID fingerprint authentication and hardware key storage
- AES-256 crypto engine in the DMA path between flash storage and main memory
- UID and GID keys fused during manufacturing (not software-readable)

### Other SoC Blocks

- **Interrupt controller**: Apple AIC (Apple Interrupt Controller), compatible string `apple,t7001-aic`
- **IOMMU**: DART (Device Address Resolution Table) — page-table-based IOMMU for peripherals
- **USB**: Likely Synopsys DesignWare (DWC) OTG controller (consistent across Apple SoCs)
- **Image Signal Processor (ISP)**: Integrated, handles camera pipeline
- **Video encoder/decoder**: Hardware H.264/H.265 codec

## 2. Display

### Panel Specifications

- **Size**: 9.7 inches diagonal
- **Resolution**: 2048 x 1536 pixels (264 PPI)
- **Technology**: IPS LCD with anti-reflective coating
- **Color**: Full sRGB coverage
- **Construction**: Fully laminated (display, digitizer, and cover glass bonded as single unit)

### Display Controller

- **LCD Driver IC**: Parade Technologies DP675
  - Likely an eDP (embedded DisplayPort) timing controller (TCON)
  - Parade Technologies specializes in eDP TCSoCs for high-resolution panels
- **LCD Bias IC**: Texas Instruments TPS65143A
  - Provides voltage rails for the LCD panel (positive/negative bias voltages)
- **Interface to SoC**: eDP (embedded DisplayPort)
  - Confirmed by third-party controller board products (QAREQU and others) that drive the iPad Air 2 panel via eDP input
  - Earlier iPads (iPad 3/4/Air 1) also use eDP for Retina displays

### Linux Framebuffer Status

- Konrad Dybcio and Markuss Broks achieved a working framebuffer on iPad Air 2 running Linux 5.18 (June 2022)
- The framebuffer is set up by pongoOS before Linux handoff; Linux inherits the pre-configured framebuffer via the `simplefb` (simple framebuffer) mechanism or EFI framebuffer
- Markuss Broks submitted patches to add generic framebuffer support to the EFI earlycon driver, tested on iPad Air 2
- No native Linux DRM/KMS driver exists for the eDP pipeline on Apple A-series SoCs

## 3. Touch Controller

### Digitizer IC

- **Chip**: Broadcom BCM5976 (codename "Cumulus")
- **Package**: 63 pins
- **Board positions**: U6600 / U6650 (varies by board revision)
- **Used in**: iPhone 5 through 6 Plus, iPad Air 1/2, iPad Mini 1-4
- **Capabilities**: Multi-touch capacitive digitizer controller

### Interface

- **Protocol**: SPI (Serial Peripheral Interface)
- **Data format**: Likely HID-over-SPI (consistent with other Apple touch controllers)
- **Note**: The Linux kernel includes a `bcm5974` driver for Apple USB multi-touch trackpads (MacBooks), but it communicates over USB HID. The iPad's BCM5976 communicates over SPI, requiring a different transport driver. The MacBook SPI keyboard/trackpad driver (`applespi` / `apple-spi`) may provide reference for the SPI transport layer.

### Reverse Engineering Status

- No public Linux driver exists for BCM5976 over SPI on iOS devices
- The USB-based `bcm5974` driver documents the multi-touch report format for earlier Broadcom touch controllers
- This is a significant driver gap for Linux on iPad

### Touch ID Sensor

- **Chip**: NXP Semiconductors 8416A1
- **Function**: Fingerprint sensor (home button)
- **Interface**: Communicates with Secure Enclave in A8X
- **Linux relevance**: Low priority; Secure Enclave pairing makes this effectively unusable without Apple's key material

## 4. WiFi / Bluetooth

### WiFi Module

- **Module**: Murata 339S02541 (Murata-packaged module containing Broadcom silicon)
- **Broadcom SoC inside**: BCM4354 (based on teardown cross-referencing and Caltech v. Apple lawsuit filings)
- **WiFi standard**: 802.11a/b/g/n/ac (Wi-Fi 5)
- **MIMO**: 2x2 MIMO (two spatial streams)
- **Channel bandwidth**: Up to 80 MHz
- **PHY rate**: Up to 867 Mbps
- **Bands**: 2.4 GHz and 5 GHz
- **Bluetooth**: 4.0 (spec from Apple; BCM4354 silicon supports up to BT 4.1)
- **Interface to SoC**: Likely SDIO (for WiFi) and UART (for Bluetooth), consistent with Broadcom combo chips in mobile devices

### Linux Driver Status

- **WiFi driver**: `brcmfmac` (Broadcom FullMAC SDIO/USB driver, in mainline Linux kernel)
  - BCM4354 is listed as a supported chip ID in the brcmfmac driver
  - Requires proprietary firmware blob: `brcm/brcmfmac4354-sdio.bin`
  - Requires NVRAM calibration file: `brcm/brcmfmac4354-sdio.txt` (device-specific)
- **Bluetooth driver**: `btbcm` / `hci_uart` (Broadcom Bluetooth over UART)
  - Requires firmware file for initialization
- **Key challenge**: Obtaining the correct firmware files. Apple ships Broadcom firmware in iOS, but it must be extracted and converted. NVRAM calibration data is board-specific and may need to be extracted from the device's NVRAM partition or reverse-engineered.

### NFC

- **Chip**: NXP 65V10
- **Function**: NFC controller (used for Apple Pay in-app only; no tap-to-pay on iPad)
- **Linux relevance**: Low priority

## 5. Audio

### Audio Codec

- **Chip**: Cirrus Logic 338S1213 (Apple-branded part number; Cirrus Logic die)
- **Function**: Audio DAC/ADC codec
- **DAC resolution**: Approximately 18-bit effective dynamic range (measured)
- **Max sample rate**: 48 kHz (may be a software limitation; hardware potentially supports higher)
- **Interface to SoC**: I2S (Inter-IC Sound), with I2C control bus

### Amplifier

- **Chip**: Maxim Integrated MAX98721BEWV
- **Function**: Boosted Class D amplifier for internal speakers
- **Interface**: I2S audio data, I2C control

### Speaker Configuration

- Stereo speakers (two speaker assemblies)
- Dual microphones

### Linux Driver Status

- Cirrus Logic 338S1213: No public Linux driver. Cirrus Logic codecs in Apple devices use Apple-specific I2C register maps. Asahi Linux has reverse-engineered Cirrus Logic codecs for Apple Silicon Macs (CS42L84, etc.), but the 338S1213 is a different generation.
- MAX98721: Maxim amplifiers have some Linux support in the `max98xxx` driver family, but the MAX98721 specifically is not upstream.
- Both require device tree bindings and register documentation.

## 6. Power Management

### Main PMIC

- **Chip**: Dialog Semiconductor 343S0675 (Wi-Fi model) / 343S0674 (Cellular model)
- **Board position**: U8100
- **Function**: Main power management IC; generates all voltage rails for the SoC, memory, peripherals
- **Interface**: Likely SPI or proprietary Apple serial bus ("SPMI" or similar)
- **Linux relevance**: Critical for proper power management, sleep states, and battery charging. No public Linux driver exists. Asahi Linux has reverse-engineered Dialog PMICs for Apple Silicon Macs, but those are newer generations.

### USB/Charging Controller

- **Chip**: CBTL1610A2 (TI/NXP "Tristar")
- **Board position**: U1700 / U3500
- **Pins**: 36
- **Function**: USB multiplexer and charging controller. Manages Lightning port functions: USB data routing, charging negotiation, accessory detection
- **Used in**: iPhone 6/6 Plus, iPad Air 2
- **Linux relevance**: Required for USB communication and power delivery through Lightning port

### Power MOSFETs

- Fairchild Semiconductor FDMC 6683
- Fairchild Semiconductor FDMC 6676BZ
- Function: Power switching/regulation

### Battery

- **Capacity**: 7340 mAh (27.62 Wh)
- **Voltage**: 3.76V nominal
- **Part number**: A1547 (020-8558)
- **Chemistry**: Lithium-ion polymer
- **Charging**: Via Lightning port, up to ~12W (5V/2.4A)

## 7. USB / Lightning

### Lightning Connector

- **Connector**: Apple Lightning (8-pin, reversible)
- **USB version**: USB 2.0 (480 Mbps max)
- **USB controller in SoC**: Likely Synopsys DesignWare DWC2 OTG (USB 2.0 On-The-Go)
  - Apple SoCs consistently use Synopsys DWC IP for USB
  - The Linux kernel has a mature `dwc2` driver supporting both host and gadget modes
  - Asahi Linux uses the `dwc3` driver on Apple Silicon; the A8X likely uses the older DWC2
- **Multiplexer**: CBTL1610A2 Tristar (see Power Management section)
- **Host mode**: Supported via Lightning-to-USB camera adapter (Apple CCK accessory)
- **Device mode**: Default mode; appears as USB device to host computer

### Linux Relevance

- USB gadget mode is essential for the boot chain (checkm8 exploit enters via USB DFU)
- USB host mode enables connecting external peripherals (keyboard, ethernet adapter)
- The DWC2 driver in Linux is well-maintained and should work if the device tree correctly describes the controller

## 8. Storage

### NAND Flash

- **Chip**: SK Hynix H2JTDG8UD1BMR (in the 16 GB model; other models use different capacities)
- **Capacity**: 128 Gb (16 GB) per chip (model-dependent: 16/32/64/128 GB SKUs)
- **Controller**: ANS1 storage co-processor (ASP), integrated in the SoC
  - Apple uses proprietary NAND controllers with custom FTL (Flash Translation Layer); on ANS1 the FTL runs in the co-processor firmware
  - A7, A8 and A8X use ANS1 (`apple,s5l8960x-ans`, `apple,t7001-ans` in HoolockLinux); A11 uses NVMe
- **Encryption**: Hardware AES-256 encryption in the DMA path
  - All NAND data is encrypted at rest using keys derived from the UID fused into the SoC
  - The Secure Enclave manages key hierarchy for Data Protection classes

### Linux Relevance

- **Driver**: HoolockLinux has a WIP ANS1 driver (`drivers/block/asp.c`, branch `ans1`, 2026-09-03), not merged into its main branch and not integrated here. See [driver-gap.md](driver-gap.md#10-storage--nand).
- The NAND is not accessible as a standard eMMC or UFS device
- For Linux bringup, the standard approach is to boot entirely from a ramdisk loaded via USB, or to use USB storage, completely bypassing internal NAND
- Asahi Linux on Apple Silicon Macs uses a reverse-engineered NVMe driver (ANS2/ANS3), but those are architecturally different from the A8X's NAND controller

## 9. Sensors

### Motion Coprocessor

- **Chip**: NXP Semiconductors LPC18B1UK (Apple M8 Motion Coprocessor)
- **Core**: ARM Cortex-M3
- **Function**: Always-on, low-power sensor hub. Aggregates accelerometer, gyroscope, compass, and barometer data.
- **Interface to SoC**: Likely SPI or I2C

### Accelerometer

- **Chip**: Bosch Sensortec BMA280
- **Type**: 3-axis MEMS accelerometer
- **Interface**: I2C or SPI (BMA280 supports both)
- **Linux driver**: `bma180` driver in mainline kernel (drivers/iio/accel/bma180.c) supports BMA280

### Barometer

- **Chip**: Bosch Sensortec BMP280
- **Type**: Barometric pressure sensor + temperature
- **Interface**: I2C or SPI
- **Linux driver**: `bmp280` driver in mainline kernel (drivers/iio/pressure/bmp280-core.c)

### Gyroscope

- **Chip**: Not definitively identified from public teardowns
- **Likely candidates**: Bosch BMG160 or InvenSense MPU-6500 (both commonly found in Apple devices of this era)
- **Interface**: I2C or SPI
- **Linux driver**: If Bosch BMG160, supported by `bmg160` driver. If InvenSense, supported by `inv_mpu6050` driver.

### Ambient Light Sensor

- **Chip**: Not definitively identified from public teardowns
- **Likely candidate**: AMS/TAOS (now ams-OSRAM) or Broadcom APDS series
- **Function**: Measures ambient light for auto-brightness
- **Interface**: I2C

### Compass (Magnetometer)

- **Chip**: Not identified from public teardowns
- **Likely candidates**: AKM AK8963 or Bosch BMM150 (common in Apple devices)
- **Interface**: I2C

## 10. Cameras

### Rear Camera (iSight)

- **Resolution**: 8 MP (3264 x 2448)
- **Sensor**: Not definitively identified; likely Sony (Apple used Sony ISX014/ISX016 sensors in iPhone 6 era, and Sony sensors for most rear cameras from 2012 onward)
- **Lens**: 5-element, f/2.4 aperture
- **Features**: Autofocus, face detection, panorama (up to 43 MP), burst mode, HDR
- **Video**: 1080p at 30 fps
- **Interface to SoC**: MIPI CSI-2

### Front Camera (FaceTime HD)

- **Resolution**: 1.2 MP
- **Video**: 720p
- **Interface**: MIPI CSI-2

### Linux Relevance

- Apple's ISP (Image Signal Processor) in the A8X handles the camera pipeline
- No public Linux driver for Apple's ISP on A-series SoCs
- The cameras are low priority for initial Linux bringup

## 11. Device Tree Sources

### Upstream Linux Kernel Status

Nick Chan (towinchenmi@gmail.com) submitted a patch series "[PATCH v5 00/20] Initial device trees for A7-A11 based Apple devices" to the Linux kernel mailing list (September/October 2024, v5/v6 revisions). This series includes:

- **dt-bindings**: `apple,t7001` compatible string for A8X platform
- **SoC dtsi**: `t7001.dtsi` — base device tree include for A8X SoC (interrupt controller, serial/UART, watchdog, pinctrl, CPU definitions)
- **Board dts files**: `j81.dts` (iPad Air 2 Wi-Fi), `j82.dts` (iPad Air 2 Cellular)
- **CPU compatible string**: `apple,typhoon` (for Typhoon cores)
- **AIC compatible string**: `apple,t7001-aic` (Apple Interrupt Controller, with A7-A11 support patches)

The AIC driver (`irqchip/apple-aic`) was extended to support A7-A11 SoCs by conditionally disabling features only present on A12+:
- A7-A10: Basic AIC functionality
- A11: Adds fast IPI support
- A12+/M1+: UNCORE2 registers, EL2 support

### What the Device Trees Define (as of v6 patches)

Based on the A8 (t7000) dtsi as a reference (the A8X t7001 dtsi follows the same pattern):

| Node | Description |
|------|-------------|
| `/cpus` | 3x Typhoon cores at 1.5 GHz |
| `/soc/interrupt-controller` | Apple AIC |
| `/soc/serial` | Apple S5L UART(s) |
| `/soc/watchdog` | Apple watchdog timer |
| `/soc/pinctrl` | GPIO/pin control |
| `/timer` | ARM architected timer |

### What is NOT Yet in the Device Trees

- Display (eDP/framebuffer pipeline)
- Touch controller (BCM5976 on SPI)
- WiFi/Bluetooth (BCM4354 on SDIO)
- Audio (Cirrus Logic codec, Maxim amp)
- NAND storage controller
- USB (DWC2)
- Sensors (accelerometer, gyroscope, barometer)
- PMIC (Dialog Semiconductor)
- Cameras / ISP

### Asahi Linux Relationship

Asahi Linux targets Apple Silicon (M1/M2/M3/M4) Macs, which use a different generation of Apple SoCs. However, the architectural patterns are similar:
- AIC interrupt controller (AIC2 on M1+, original AIC on A7-A11)
- DART IOMMU
- Synopsys DWC USB controllers
- Apple UART (S5L UART)

Asahi's driver work for DART, AIC, USB, SPI, I2C, and audio codecs provides a reference, but A-series and M-series SoCs differ enough that direct code reuse is limited. Register layouts, peripheral addresses, and device tree bindings are different.

### iOS Firmware Device Trees

Apple ships device trees in iOS firmware (iBoot passes them to XNU). These can be extracted from IPSW files and decoded using tools like `devicetree-dump`. The iOS device trees contain:
- Complete peripheral address maps
- Interrupt routing
- Clock tree
- Power domain information
- Peripheral identification strings

The iPhone Wiki documents the device tree format. iOS device trees use a property-list-like binary format that differs from Linux FDT (Flattened Device Tree), but the information can be translated.

## 12. Summary: Driver Gap Matrix

| Subsystem | Chip | Linux Driver | Status |
|-----------|------|-------------|--------|
| CPU | A8X Typhoon | arm64 kernel | Works (upstream DT patches pending) |
| Interrupt controller | Apple AIC | irqchip/apple-aic | Works (upstream, A7-A11 support patched) |
| UART/serial | Apple S5L UART | apple-s5l-uart | Works (upstream) |
| Framebuffer | (pongoOS-initialized) | simplefb / efifb | Works (basic, no acceleration) |
| Display (native) | Parade DP675 + eDP | None | No driver; needs reverse engineering |
| Touch | BCM5976 (SPI) | None | No driver; major gap |
| WiFi | BCM4354 (SDIO) | brcmfmac | Driver exists; needs firmware + DT |
| Bluetooth | BCM4354 (UART) | btbcm | Driver exists; needs firmware + DT |
| Audio codec | Cirrus Logic 338S1213 | None | No driver; needs RE |
| Audio amp | MAX98721 | None | No upstream driver |
| PMIC | Dialog 343S0675 | None | No driver; critical gap |
| USB | DWC2 OTG | dwc2 | Driver exists; needs DT integration |
| NAND storage | Apple ANS1 | asp (HoolockLinux `ans1`, WIP) | Out of tree; use ramdisk/USB storage for now |
| Accelerometer | Bosch BMA280 | bma180 (IIO) | Driver exists; needs DT |
| Barometer | Bosch BMP280 | bmp280 (IIO) | Driver exists; needs DT |
| Gyroscope | Unknown (likely Bosch) | Likely exists | Needs chip ID + DT |
| GPU | PowerVR GXA6850 | pvr (Mesa, experimental) | Series 6XT partial; GXA6850 not listed |
| NFC | NXP 65V10 | nfcmrvl / nxp-nci? | Low priority |
| Camera | Sony (likely) + Apple ISP | None | No ISP driver; low priority |
| Touch ID | NXP 8416A1 | None | Secure Enclave locked; not feasible |

## 13. Key References

- iFixit iPad Air 2 Teardown: https://www.ifixit.com/Teardown/iPad+Air+2+Teardown/30592
- AnandTech A8X SoC Analysis: https://www.anandtech.com/show/8666/the-apple-ipad-air-2-review/2
- AnandTech GXA6850 GPU Analysis: https://www.anandtech.com/show/8716/apple-a8xs-gpu-gxa6850-even-better-than-i-thought
- Linux A7-A11 Device Tree Patches: https://lore.kernel.org/lkml/20240925071939.6107-3-towinchenmi@gmail.com/T/
- iPad Linux Project: https://ipadlinux.org/
- Apple AIC Driver (upstream): https://cateee.net/lkddb/web-lkddb/APPLE_AIC.html
- Mesa PowerVR Driver: https://docs.mesa3d.org/drivers/powervr.html
- BCM5974 Linux Driver (reference for touch): https://docs.kernel.org/input/devices/bcm5974.html
- Apple Platform Security Guide: https://support.apple.com/guide/security/
- PhoneDB A8X Specs: https://phonedb.net/index.php?m=processor&id=548&c=apple_a8x_apl1012__t7001
