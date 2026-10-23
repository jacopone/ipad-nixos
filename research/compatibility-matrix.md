# checkm8 iPad Compatibility Matrix

Comprehensive list of every iPad model vulnerable to checkm8 (A5 through A11 SoCs),
with hardware specifications and Linux support status.

Sources: Apple tech specs, iFixit teardowns, Nick Chan's kernel device tree patches
(v6, October 2024), HoolockLinux feature documentation, The Apple Wiki, postmarketOS wiki.

---

## Important Notes

**32-bit vs 64-bit**: The A5, A5X, A6, and A6X SoCs are 32-bit ARMv7. The A7 through A11
are 64-bit ARMv8-A (AArch64). All current Linux bring-up work (Nick Chan / HoolockLinux /
Konrad Dybcio) targets AArch64 only (A7+). The 32-bit iPads are checkm8-vulnerable but
have no Linux device tree work and are not practical targets.

**Connector transition**: The 30-pin dock connector was used through iPad 3 (3rd gen).
Lightning was introduced with iPad 4 (4th gen) and iPad Mini 1 in late 2012.

---

## Generation 1: Apple A5 / A5X (2011-2012) -- 32-bit, No Linux Support

### A5 (S5L8940X / S5L8942X / S5L8947X)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad 2 (Wi-Fi) | iPad2,1 | K93 | A5 | 512 MB | 2011 | 9.7" | 1024x768 | 30-pin | Wi-Fi only |
| iPad 2 (GSM) | iPad2,2 | K94 | A5 | 512 MB | 2011 | 9.7" | 1024x768 | 30-pin | Wi-Fi + Cellular |
| iPad 2 (CDMA) | iPad2,3 | K95 | A5 | 512 MB | 2011 | 9.7" | 1024x768 | 30-pin | Wi-Fi + Cellular |
| iPad 2 (Rev A) | iPad2,4 | K93a | A5 (die-shrink) | 512 MB | 2012 | 9.7" | 1024x768 | 30-pin | Wi-Fi only |
| iPad Mini (Wi-Fi) | iPad2,5 | P105 | A5 (die-shrink) | 512 MB | 2012 | 7.9" | 1024x768 | Lightning | Wi-Fi only |
| iPad Mini (GSM) | iPad2,6 | P106 | A5 (die-shrink) | 512 MB | 2012 | 7.9" | 1024x768 | Lightning | Wi-Fi + Cellular |
| iPad Mini (CDMA) | iPad2,7 | P107 | A5 (die-shrink) | 512 MB | 2012 | 7.9" | 1024x768 | Lightning | Wi-Fi + Cellular |

### A5X (S5L8945X)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad 3 (Wi-Fi) | iPad3,1 | J1 | A5X | 1 GB | 2012 | 9.7" | 2048x1536 | 30-pin | Wi-Fi only |
| iPad 3 (CDMA) | iPad3,2 | J2 | A5X | 1 GB | 2012 | 9.7" | 2048x1536 | 30-pin | Wi-Fi + Cellular |
| iPad 3 (GSM) | iPad3,3 | J2a | A5X | 1 GB | 2012 | 9.7" | 2048x1536 | 30-pin | Wi-Fi + Cellular |

**Linux status**: None. 32-bit ARMv7. No device tree work exists. checkm8-a5 exploit
variant works but requires different tooling (Raspberry Pi Pico for A5/A5X DFU). Not a
practical Linux target due to 32-bit architecture, 512 MB - 1 GB RAM, and lack of any
existing bring-up work.

---

## Generation 2: Apple A6X (2012) -- 32-bit, No Linux Support

### A6X (S5L8955X)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad 4 (Wi-Fi) | iPad3,4 | P101 | A6X | 1 GB | 2012 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad 4 (GSM) | iPad3,5 | P102 | A6X | 1 GB | 2012 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |
| iPad 4 (Global) | iPad3,6 | P103 | A6X | 1 GB | 2012 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |

Note: No A6 (non-X) iPads exist. The A6 was used only in iPhone 5 and iPhone 5c.

**Linux status**: None. 32-bit ARMv7. Same limitations as A5/A5X generation.

---

## Generation 3: Apple A7 (2013-2014) -- 64-bit, Linux Device Trees Upstream

### A7 (S5L8960X / S5L8965X)

The iPad Air variant uses S5L8965X internally but is treated as S5L8960X by software.

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad Air (Wi-Fi) | iPad4,1 | J71 | A7 | 1 GB | 2013 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Air (Cellular) | iPad4,2 | J72 | A7 | 1 GB | 2013 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |
| iPad Air (China) | iPad4,3 | J73 | A7 | 1 GB | 2013 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular (TD-LTE) |
| iPad Mini 2 (Wi-Fi) | iPad4,4 | J85 | A7 | 1 GB | 2013 | 7.9" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Mini 2 (Cellular) | iPad4,5 | J86 | A7 | 1 GB | 2013 | 7.9" | 2048x1536 | Lightning | Wi-Fi + Cellular |
| iPad Mini 2 (China) | iPad4,6 | J87 | A7 | 1 GB | 2013 | 7.9" | 2048x1536 | Lightning | Wi-Fi + Cellular (TD-LTE) |
| iPad Mini 3 (Wi-Fi) | iPad4,7 | J85m | A7 | 1 GB | 2014 | 7.9" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Mini 3 (Cellular) | iPad4,8 | J86m | A7 | 1 GB | 2014 | 7.9" | 2048x1536 | Lightning | Wi-Fi + Cellular |
| iPad Mini 3 (China) | iPad4,9 | J87m | A7 | 1 GB | 2014 | 7.9" | 2048x1536 | Lightning | Wi-Fi + Cellular (TD-LTE) |

**Linux status (HoolockLinux)**:
- Device trees: upstream in Linux 6.13
- Main display (simple-framebuffer): upstream in Linux 6.13
- Brightness control: in linux-apple branch
- Buttons (gpio-keys): upstream in Linux 6.13
- SMP spin-up: upstream in Linux 6.13
- UART, GPIO, watchdog, I2C, cpufreq: upstream across 6.12-6.18
- USB2 device mode: in linux-apple branch
- Touch, WiFi, GPU, audio: TBA (not yet working)

**Hardware notes**: iPad Mini 3 is identical to iPad Mini 2 internally except for the
addition of Touch ID. Same SoC, same RAM, same display, same touch controller (BCM5976).
All A7 iPads use the Broadcom BCM5976 touch controller.

---

## Generation 4: Apple A8 / A8X (2014-2015) -- 64-bit, Linux Device Trees Upstream

### A8 (T7000)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad Mini 4 (Wi-Fi) | iPad5,1 | J96 | A8 | 2 GB | 2015 | 7.9" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Mini 4 (Cellular) | iPad5,2 | J97 | A8 | 2 GB | 2015 | 7.9" | 2048x1536 | Lightning | Wi-Fi + Cellular |

Note: No full-size A8 (non-X) iPad exists. The A8 was also used in iPhone 6, iPhone 6
Plus, and iPod touch 6.

### A8X (T7001)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad Air 2 (Wi-Fi) | iPad5,3 | J81 | A8X | 2 GB | 2014 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Air 2 (Cellular) | iPad5,4 | J82 | A8X | 2 GB | 2014 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |

**Linux status (HoolockLinux)**:
- Device trees (A8 and A8X): upstream in Linux 6.13
- Main display (simple-framebuffer): upstream in Linux 6.13
- Brightness control: A8 devices upstream in 6.15; A8X in linux-apple branch
- Buttons (gpio-keys): upstream in Linux 6.13
- SMP spin-up: upstream in Linux 6.13
- UART, GPIO, watchdog, I2C, cpufreq: upstream across 6.12-6.18
- USB2 device mode: in linux-apple branch
- Touch, WiFi, GPU, audio: TBA (not yet working)

**Hardware notes**: iPad Mini 4 is internally a miniaturized iPad Air 2 according to iFixit
teardowns. Both use:
- Touch controller: Broadcom BCM5976 ("Cumulus")
- Wi-Fi module: Murata 339S02541 (iPad Air 2) / USI 339S00045 (iPad Mini 4) -- both
  contain Broadcom BCM43xx series chipsets
- Display driver: Parade Technologies (DP675 in iPad Air 2)

The A8X is exclusive to the iPad Air 2 (tri-core, wider memory bus). The A8 in the
iPad Mini 4 is the standard dual-core variant.

---

## Generation 5: Apple A9 / A9X (2015-2017) -- 64-bit, Linux Device Trees Upstream

### A9 (S8000 Samsung / S8003 TSMC)

Two manufacturing variants exist. Device trees cover both. iPad 5 ships with either.

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad 5 (Wi-Fi) | iPad6,11 | J71s/J71t | A9 | 2 GB | 2017 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad 5 (Cellular) | iPad6,12 | J72s/J72t | A9 | 2 GB | 2017 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |

Note: The "s" suffix denotes Samsung A9, "t" denotes TSMC A9. Both are supported.

### A9X (S8001)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad Pro 12.9" (1st gen, Wi-Fi) | iPad6,7 | J98a | A9X | 4 GB | 2015 | 12.9" | 2732x2048 | Lightning | Wi-Fi only |
| iPad Pro 12.9" (1st gen, Cell) | iPad6,8 | J99a | A9X | 4 GB | 2015 | 12.9" | 2732x2048 | Lightning | Wi-Fi + Cellular |
| iPad Pro 9.7" (Wi-Fi) | iPad6,3 | J127 | A9X | 2 GB | 2016 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad Pro 9.7" (Cellular) | iPad6,4 | J128 | A9X | 2 GB | 2016 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |

Note: iPad Pro 12.9" (1st gen) has 4 GB RAM. iPad Pro 9.7" has only 2 GB RAM despite
using the same A9X chip.

**Linux status (HoolockLinux)**:
- Device trees (A9 and A9X): upstream in Linux 6.13
- Main display (simple-framebuffer): upstream in Linux 6.13
- Brightness control: A9 devices upstream in 6.15; A9X in linux-apple branch
- Buttons (gpio-keys): upstream in Linux 6.13
- SMP spin-up: upstream in Linux 6.13
- UART, GPIO, watchdog, I2C, cpufreq: upstream across 6.12-6.18
- USB2 device mode: in linux-apple branch
- Touch, WiFi, GPU, audio: TBA (not yet working)

**Hardware notes**: iPad Pro 9.7" uses different touch hardware from the standard iPads.
The Pro line uses a Parade Technologies DP815 touch/display controller instead of the
Broadcom BCM5976 used in non-Pro iPads. The iPad Pro 12.9" is the only iPad with 4 GB RAM
in this generation. The iPad 5 (2017) reuses much of the iPad Air 1 chassis design with
the A9 chip -- it still uses the BCM5976 touch controller.

---

## Generation 6: Apple A10 / A10X (2017-2019) -- 64-bit, Linux Device Trees Upstream

### A10 Fusion (T8010)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad 6 (Wi-Fi) | iPad7,5 | J71b | A10 Fusion | 2 GB | 2018 | 9.7" | 2048x1536 | Lightning | Wi-Fi only |
| iPad 6 (Cellular) | iPad7,6 | J72b | A10 Fusion | 2 GB | 2018 | 9.7" | 2048x1536 | Lightning | Wi-Fi + Cellular |
| iPad 7 (Wi-Fi) | iPad7,11 | J171 | A10 Fusion | 3 GB | 2019 | 10.2" | 2160x1620 | Lightning | Wi-Fi only |
| iPad 7 (Cellular) | iPad7,12 | J172 | A10 Fusion | 3 GB | 2019 | 10.2" | 2160x1620 | Lightning | Wi-Fi + Cellular |

Note: iPad 7 is the first standard iPad with 3 GB RAM and a 10.2" display.

### A10X Fusion (T8011)

| Marketing Name | Model ID | Codename | SoC | RAM | Year | Screen | Resolution | Connector | Variants |
|---|---|---|---|---|---|---|---|---|---|
| iPad Pro 10.5" (Wi-Fi) | iPad7,3 | J207 | A10X Fusion | 4 GB | 2017 | 10.5" | 2224x1668 | Lightning | Wi-Fi only |
| iPad Pro 10.5" (Cellular) | iPad7,4 | J208 | A10X Fusion | 4 GB | 2017 | 10.5" | 2224x1668 | Lightning | Wi-Fi + Cellular |
| iPad Pro 12.9" 2nd gen (Wi-Fi) | iPad7,1 | J120 | A10X Fusion | 4 GB | 2017 | 12.9" | 2732x2048 | Lightning | Wi-Fi only |
| iPad Pro 12.9" 2nd gen (Cell) | iPad7,2 | J121 | A10X Fusion | 4 GB | 2017 | 12.9" | 2732x2048 | Lightning | Wi-Fi + Cellular |

**Linux status (HoolockLinux)**:
- Device trees (A10 and A10X): upstream in Linux 6.13
- Main display (simple-framebuffer): upstream in Linux 6.13
- Brightness control: A10 upstream in 6.15; A10X in linux-apple branch
- Buttons (gpio-keys): upstream in Linux 6.13
- SMP spin-up: upstream in Linux 6.13
- cpufreq: upstream in 6.2 (driver) / 6.15 (dts) -- A10 has big.LITTLE heterogeneous
  design with performance and efficiency cores
- UART, GPIO, watchdog, I2C: upstream across 6.12-6.18
- USB2 device mode: in linux-apple branch
- Touch, WiFi, GPU, audio: TBA (not yet working)
- "Fake Home Button": TBA on iPhone 7/7+ (not applicable to iPads)

**Hardware notes**: The A10 Fusion is Apple's first big.LITTLE chip with 2 performance +
2 efficiency cores. The A10X Fusion has 3 performance + 3 efficiency cores. iPad Pro 10.5"
and 12.9" (2nd gen) support ProMotion (120 Hz refresh). The iPad 7 is the first iPad with
a 10.2" screen -- a kernel/DT built for iPad 6 would not work directly on iPad 7 due to
different display panel and resolution.

---

## Generation 7: Apple A11 Bionic (2017) -- 64-bit, Linux Device Trees Upstream

### A11 Bionic (T8015)

**No A11-based iPads exist.** The A11 was used only in:
- iPhone 8 (D20 / D201)
- iPhone 8 Plus (D21 / D211)
- iPhone X (D22 / D221)

These are included in Nick Chan's device tree patches and HoolockLinux, but they are
iPhones, not iPads. The A11 is notable for being the last SoC affected by checkm8 and
the first Apple chip with a Neural Engine. It also has NVMe internal storage support in
Linux (upstream 6.18), which A7-A10X devices lack.

---

## Summary: All checkm8-Vulnerable iPads

### Count by SoC

| SoC | Architecture | iPad Models | Linux DTs | Practical for Linux |
|---|---|---|---|---|
| A5 | 32-bit ARMv7 | 7 (iPad 2 x4, iPad Mini 1 x3) | No | No |
| A5X | 32-bit ARMv7 | 3 (iPad 3 x3) | No | No |
| A6X | 32-bit ARMv7 | 3 (iPad 4 x3) | No | No |
| A7 | 64-bit ARMv8 | 9 (iPad Air x3, iPad Mini 2 x3, iPad Mini 3 x3) | Yes (6.13) | Yes (1 GB RAM is limiting) |
| A8 | 64-bit ARMv8 | 2 (iPad Mini 4 x2) | Yes (6.13) | Yes |
| A8X | 64-bit ARMv8 | 2 (iPad Air 2 x2) | Yes (6.13) | Yes (primary target) |
| A9 | 64-bit ARMv8 | 2 (iPad 5 x2) | Yes (6.13) | Yes |
| A9X | 64-bit ARMv8 | 4 (iPad Pro 12.9" x2, iPad Pro 9.7" x2) | Yes (6.13) | Yes |
| A10 | 64-bit ARMv8 | 4 (iPad 6 x2, iPad 7 x2) | Yes (6.13) | Yes |
| A10X | 64-bit ARMv8 | 4 (iPad Pro 10.5" x2, iPad Pro 12.9" 2nd x2) | Yes (6.13) | Yes |
| A11 | 64-bit ARMv8 | 0 (iPhones only) | Yes (6.13) | N/A for iPads |

**Total checkm8-vulnerable iPad models: 40** (counting Wi-Fi/Cellular/China variants)
**Total with Linux device trees: 27** (all A7-A10X iPads)
**Total 32-bit (not practical): 13** (A5/A5X/A6X)

---

## Linux Feature Status Summary (A7-A10X iPads)

| Feature | Status | Notes |
|---|---|---|
| Boot via pongoOS | Working | All A7-A10X |
| SMP (all CPU cores) | Upstream 6.13 | spin-table method |
| UART (serial console) | Upstream 6.13 | via USB serial |
| Simple framebuffer | Upstream 6.13 | Display output works on all iPads |
| Brightness control | Upstream 6.15 / linux-apple | Varies by device |
| Buttons (power, volume) | Upstream 6.13 | gpio-keys on A7-A10 |
| cpufreq | Upstream 6.14-6.15 | Frequency scaling works |
| I2C | Upstream 6.18 | Bus access for peripherals |
| USB2 device mode | linux-apple branch | For serial console / networking |
| Watchdog | Upstream 6.13 | Hardware watchdog timer |
| RTC | linux-apple branch | Real-time clock |
| Touch input | TBA | No driver yet |
| WiFi | TBA | No driver yet |
| Bluetooth | TBA | No driver yet |
| GPU acceleration | TBA | PowerVR, no open-source driver |
| Audio | TBA | No driver yet |
| Display pipe (proper DRM/KMS) | TBA | Currently simple-framebuffer only |
| Camera | TBA | No driver yet |
| NVMe storage | A11 only (6.18) | Not available on A7-A10X |
| ANS1 storage (A7, A8, A8X) | WIP (HoolockLinux `ans1` branch) | Out of tree, see driver-gap.md |

---

## Hardware Variation Analysis

### Touch Controllers

| Touch Controller | iPad Models Using It |
|---|---|
| Broadcom BCM5976 ("Cumulus") | iPad Air, iPad Air 2, iPad Mini 1/2/3/4, iPad 5 (2017) |
| Parade Technologies DP815 | iPad Pro 9.7", iPad Pro 10.5", iPad Pro 12.9" (1st and 2nd gen) |
| Unknown (likely BCM-derived) | iPad 6 (2018), iPad 7 (2019) -- uses two Broadcom touch ICs per iFixit |

The BCM5976 is used across a wide range of models from iPhone 5 through iPad 5 (2017).
A single reverse-engineered touch driver for BCM5976 would cover most non-Pro iPads.
The iPad Pro line uses different Parade Technologies touch controllers, requiring
separate driver work.

### WiFi Modules

| WiFi Module | Broadcom Chipset | iPad Models |
|---|---|---|
| Murata 339S0171 | BCM4334 (802.11 a/b/g/n) | iPad 4, iPad Mini 1 |
| USI 339S0213 | BCM4334 variant | iPad Air |
| Murata 339S02541 | BCM43xx (802.11ac) | iPad Air 2 |
| USI 339S00045 | BCM43xx (802.11ac) | iPad Mini 4 |
| Apple/USI 339S0038x | BCM43xx (802.11ac) | iPad 5 (2017) |
| Unknown USI/Murata | BCM43xx | iPad 6, iPad 7, iPad Pro models |

All WiFi modules use Broadcom chipsets. The Linux brcmfmac driver supports many Broadcom
WiFi chips, but Apple's modules use custom firmware and possibly custom pinouts. Firmware
extraction from the iOS filesystem may be necessary. This is a shared problem across all
checkm8 iPads -- solving WiFi for one likely solves it for most.

### Display Panels

| Resolution | Screen Size | iPad Models |
|---|---|---|
| 1024x768 | 9.7" | iPad 2 |
| 1024x768 | 7.9" | iPad Mini 1 |
| 2048x1536 | 9.7" | iPad 3, 4, Air, Air 2, 5, 6, Pro 9.7" |
| 2048x1536 | 7.9" | iPad Mini 2, 3, 4 |
| 2160x1620 | 10.2" | iPad 7 |
| 2224x1668 | 10.5" | iPad Pro 10.5" |
| 2732x2048 | 12.9" | iPad Pro 12.9" (1st and 2nd gen) |

Most iPads with Linux support share 2048x1536 resolution. The simple-framebuffer driver
currently works regardless of resolution. A proper DRM/KMS display pipe driver will need
per-panel configuration but the display controller IP is shared within each SoC generation.

### SoC Hardware Sharing

**Question: Would a kernel + device tree for one model work on another with the same SoC?**

Within the same SoC, the kernel image is identical. What changes is the device tree (.dtb),
which describes the specific board layout. Key differences between models on the same SoC:

| Same SoC, Different... | Requires different DT? | Example |
|---|---|---|
| Wi-Fi vs Cellular variant | Yes (cellular modem node) | iPad Air 2 Wi-Fi vs Cellular |
| Same screen size, same year | Usually identical DT | iPad Mini 2 Wi-Fi variants |
| Different screen size | Yes (display panel, backlight) | iPad 6 (9.7") vs iPad 7 (10.2") |
| Different RAM amount | Sometimes (memory nodes) | iPad Pro 9.7" (2 GB) vs Pro 12.9" (4 GB) |

Each specific model variant already has its own .dts file in the kernel patches.

---

## Recommended Expansion Path from iPad Air 2

### Tier 1: Share the most hardware with iPad Air 2 (A8X)

| Model | Why | Effort |
|---|---|---|
| **iPad Mini 4** | Same generation, same touch controller (BCM5976), same WiFi chipset family, nearly identical internals per iFixit. Different SoC (A8 vs A8X) but A8 DT already exists. | Very low -- DTs already upstream, just need same peripheral drivers |
| **iPad Air (1st gen)** | Same 9.7" 2048x1536 display, same touch controller (BCM5976). A7 SoC. Only 1 GB RAM limits usability. | Low -- DTs upstream, 1 GB RAM is the constraint |

### Tier 2: Same touch controller family, good specs

| Model | Why | Effort |
|---|---|---|
| **iPad 5 (2017)** | BCM5976 touch, A9, 2 GB RAM, 9.7" 2048x1536. Reuses iPad Air chassis. | Low -- touch driver from Air 2 should transfer directly |
| **iPad Mini 2/3** | BCM5976 touch, A7, 1 GB RAM. Mini 3 adds Touch ID (irrelevant for Linux). | Low -- but 1 GB RAM is limiting |

### Tier 3: Good specs, different peripherals

| Model | Why | Effort |
|---|---|---|
| **iPad 6 (2018)** | A10, 2 GB RAM, 9.7" display. Touch controller uses Broadcom ICs but may differ from BCM5976. | Medium -- A10 big.LITTLE adds complexity |
| **iPad 7 (2019)** | A10, 3 GB RAM (best non-Pro). 10.2" display (different panel). | Medium -- best non-Pro specs but different display |
| **iPad Pro 10.5"** | A10X, 4 GB RAM, 120 Hz ProMotion. Different touch controller (Parade). | Medium-high -- best specs, but Pro peripherals differ |
| **iPad Pro 12.9" (2nd gen)** | A10X, 4 GB RAM, 120 Hz. Largest display. | Medium-high -- same as Pro 10.5" concerns |

### Tier 4: Usable but limited or complex

| Model | Why | Effort |
|---|---|---|
| **iPad Pro 12.9" (1st gen)** | A9X, 4 GB RAM. Good specs but large and early Pro. | Medium -- A9X DT exists |
| **iPad Pro 9.7"** | A9X, only 2 GB RAM. Different touch from non-Pro. | Medium -- no RAM advantage over Air 2 |
| **iPad 2, 3, 4, Mini 1** | 32-bit, low RAM, no Linux work. | Not recommended |

---

## Key Takeaways

1. **27 iPad model variants** (A7 through A10X) have upstream Linux device trees as of
   kernel 6.13, with ongoing feature additions through 6.18+.

2. **Display output works on all of them** via simple-framebuffer. Brightness control is
   also upstream or in the linux-apple branch for all models.

3. **The biggest gaps** are touch input, WiFi, GPU, and audio -- none of these work on
   any checkm8 iPad yet. These are the critical drivers needed for usability.

4. **Touch controller uniformity** is good for non-Pro iPads: the Broadcom BCM5976 covers
   iPad Air, Air 2, Mini 1/2/3/4, and iPad 5. Solving touch for one solves it for many.

5. **iPad Pro models use different touch hardware** (Parade Technologies) and would require
   separate driver work.

6. **WiFi uses Broadcom chipsets across all models** but with custom Apple firmware. This
   is a shared challenge that, once solved, benefits all models.

7. **Best second target after iPad Air 2**: iPad Mini 4 (nearly identical internals) or
   iPad 5 2017 (same touch controller, better SoC, same RAM).

8. **Best overall specs**: iPad 7 (3 GB RAM, A10 Fusion) or iPad Pro 10.5"/12.9" 2nd gen
   (4 GB RAM, A10X Fusion, 120 Hz display).
