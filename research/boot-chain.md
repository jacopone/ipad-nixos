# Boot Chain Documentation: checkm8 to Linux on iPad Air 2

Full boot path from checkm8 exploit through pongoOS to Linux kernel on iPad Air 2 (A8X/t7001).
Research conducted February 2026.

## 1. DFU Mode and checkm8 Exploit Mechanics

### DFU Mode Overview

Device Firmware Upgrade (DFU) is the lowest-level recovery mode on iOS devices. It runs
entirely within SecureROM (BootROM), the first code executed when the SoC powers on. DFU
accepts firmware images over USB for flashing. Enter DFU mode via a specific physical button
sequence while powered off and connected to a host computer.

In DFU mode, the device:
- Enumerates as a USB device (Vendor ID 0x05AC, Product ID varies by chip)
- Accepts only USB Control Transfers (Setup -> Data -> Status phases)
- Allocates a global I/O buffer for receiving firmware data
- Registers a DFU interface handler for all USB transfers
- Waits for a signed firmware image, verifies its signature, and boots it

### The checkm8 Vulnerability (CVE-2019-8900)

checkm8 exploits a use-after-free vulnerability in the USB DFU stack of Apple's SecureROM.
The bug: when DFU exits abnormally, it frees its I/O buffer but does not clear the global
pointer to that buffer. On DFU re-entry, the stale pointer references freed memory.

### Exploitation Steps

**Step 1 -- Trigger incomplete data transfer:**
An attacker sends a USB Setup packet to begin a data transfer, then aborts the transfer
before completion (by issuing a DFU abort or USB reset). This puts the DFU state machine
into a transitional state where the data phase has started but not finished.

**Step 2 -- Force DFU re-entry:**
A USB reset or DFU_CLR_STATUS request causes SecureROM to restart the DFU cycle. The DFU
shutdown code frees the I/O buffer. However, because the data transfer was incomplete, the
USB stack does not clear the global variable pointing to the now-freed buffer.

**Step 3 -- Heap feng shui (heap grooming):**
Before exploiting the dangling pointer, the attacker grooms the heap so that the next DFU
iteration allocates its I/O buffer at a different address from the freed one. This prevents
the freed memory from being immediately reused for the new I/O buffer. Three types of USB
requests control the heap layout:
- "stall" requests: cancelled immediately, consume heap space
- "leak" requests: normal transfers that allocate and free predictably
- "no_leak" requests: alter the heap allocator's free-list behavior

**Step 4 -- Overwrite callback pointer:**
With the heap groomed, the attacker sends data that writes into the freed buffer region.
A `usb_device_io_request` structure lands in the freed memory. The attacker overwrites two
fields in this structure:
- The callback function pointer (redirected to attacker payload address)
- The "next" pointer in the linked list (set to NULL to prevent the device from trying to
  free subsequent request objects and crashing)

**Step 5 -- Trigger payload execution:**
When the USB stack finishes processing the request, it calls the callback function pointer.
Control flow redirects to the attacker's payload, which now runs at SecureROM privilege level.

### What the Payload Can Do

At this point, the attacker has arbitrary code execution in the BootROM context. This means:
- Full control over the boot chain from the earliest point
- Ability to load unsigned code (bypass SecureROM signature checks)
- Load a custom second-stage bootloader (pongoOS)
- Read/write all memory accessible to the BootROM
- Cannot bypass Secure Enclave Processor (SEP), which is a separate coprocessor
- Cannot read hardware-fused keys (UID/GID) directly, only use them via the AES engine

### Tethered Boot: Practical Implications

checkm8 is a tethered exploit. "Tethered" means:
- The exploit state is not persistent across reboots
- Every time the device powers off or reboots, the exploit must be re-executed
- Re-execution requires a USB connection to a host computer running the exploit tool
- The host computer must put the device into DFU mode and re-run the full exploit sequence

For a Linux workstation use case (iPad as a daily-use device), this means:
- Every power-on requires: plug iPad into host PC -> enter DFU mode -> run exploit -> load
  pongoOS -> load Linux kernel/DT/initramfs -> boot
- The process takes approximately 10-30 seconds depending on tooling
- If the iPad crashes or runs out of battery, it must be re-tethered to boot again
- An automation script can reduce this to a single command on the host side

### Devices Affected

The vulnerability affects all Apple SoCs from A5 through A11:
- A12 and later have the same use-after-free in ROM, but the memory leak needed to exploit
  it was made unreachable in A12 silicon, making exploitation impossible

The iPad Air 2 (A8X/t7001) is squarely in the vulnerable range.

### Tools Implementing checkm8

| Tool | Language | Notes |
|------|----------|-------|
| ipwndfu | Python | Original by axi0mX, MIT license |
| gaster | C | Fast, lightweight, MIT license |
| Achilles | C | A7-A11 utility, MIT, supports serial output and pongoOS boot |
| checkra1n | C/C++ | Binary-only, includes pongoOS |
| palera1n | Shell/C | Open source, uses checkra1n 0.1337.x builds |

Achilles is notable for its `-S` flag (enable serial output) and `-p` flag (boot to pongoOS
and exit), making it suitable for Linux boot workflows.

Sources:
- https://theapplewiki.com/wiki/Checkm8_Exploit
- https://alfiecg.uk/2023/07/21/A-comprehensive-write-up-of-the-checkm8-BootROM-exploit.html
- https://habr.com/en/companies/dsec/articles/472762/
- https://github.com/alfiecg24/Achilles

---

## 2. pongoOS Boot Sequence

### What pongoOS Is

pongoOS is a pre-boot execution environment for Apple devices, loaded via the checkm8
exploit. It runs at EL1 (kernel privilege level) on the application processor and provides:
- Interactive shell accessible over USB (via `pongoterm` client) or UART
- Module loading system with 500+ exported API symbols
- Cooperative multitasking with preemption support
- Physical and virtual memory management
- Hardware initialization for the specific SoC detected at boot
- Ability to boot XNU (iOS), Linux, or custom payloads

### How pongoOS Gets Loaded

1. Host computer runs a checkm8 tool (Achilles, checkra1n, etc.)
2. The tool exploits the BootROM and gains code execution
3. The tool sends the pongoOS binary (`Pongo.bin`) over USB to the device
4. The BootROM executes pongoOS as the next stage of the boot chain

### pongoOS Internal Boot Sequence

Once pongoOS starts executing:

**Phase 1 -- Assembly entry (`entry.S`):**
- Sets up the initial stack
- Transitions to C code via `trampoline_entry()`

**Phase 2 -- Trampoline decision:**
- Determines whether to patch the bootloader (iBoot) or proceed with kernel init
- If patching: disables DRAM clearing, prevents RVBAR locking, preserves AES keys, unlocks
  the reconfiguration engine

**Phase 3 -- Kernel initialization:**
- Sets up the MMU (Memory Management Unit)
- Parses the Apple Device Tree passed by iBoot to discover hardware capabilities
- Detects the specific SoC variant (t7000, t7001, t8010, etc.) from the device tree
- Initializes physical page allocator (16KB pages) and virtual memory
- Starts the task scheduler

**Phase 4 -- Main task execution:**
- Initializes hardware drivers (USB via Synopsys OTG controller, UART, etc.)
- Starts the interactive shell
- Waits for commands from USB (`pongoterm`) or UART

**Phase 5 -- Boot target selection:**
- Based on `gBootFlag`, boots XNU (iOS), Linux, or custom image
- `BOOT_FLAG_LINUX` triggers the Linux boot path

### The Module System

pongoOS supports runtime extensibility through loadable modules:
- Modules are compiled separately and loaded via the `modload` shell command
- Each module can register custom shell commands
- Modules interact with pongoOS through an exported symbol table (500+ APIs)
- The Kernel Patch Framework (KPF) is itself a module (`checkra1n-kpf-pongo`)
- KPF is relevant only for iOS boot (patches XNU kernel), not for Linux boot

### USB Interface

pongoOS initializes the Synopsys OTG USB controller present in Apple SoCs. This provides:
- USB device enumeration (Vendor 0x05AC, Product 0x4141)
- File transfer capability (used to receive kernel, device tree, initramfs)
- Interactive shell access via the `pongoterm` client tool
- Commands sent as USB control transfers (bmRequestType 0x21)

### Device Tree Handling

pongoOS parses the Apple Device Tree (ADT) that is passed by the bootloader (iBoot):
- The ADT is Apple's proprietary format, structurally similar to Open Firmware device trees
- pongoOS extracts: ARM IO base address, memory layout, SoC type, peripheral configurations
- This information drives hardware initialization and SoC-specific code paths
- For Linux boot, a separate Flattened Device Tree (FDT/DTB) in standard Linux format must
  be provided -- pongoOS does not convert the Apple DT to Linux FDT automatically

Sources:
- https://github.com/checkra1n/PongoOS
- https://deepwiki.com/checkra1n/PongoOS/1-overview
- https://github.com/checkra1n/PongoOS/blob/master/scripts/load_linux.py

---

## 3. Linux Kernel Loading and Handoff

### The load_linux.py Script

pongoOS up to tag 2.6.3 includes `scripts/load_linux.py`, a Python script that automates
Linux kernel loading over USB. It communicates with pongoOS using USB control transfers.
`boot/load_linux.py` is based on the 2.6.1 version and adds a read of the
pongoOS stdout buffer after every command, so a rejected command aborts the upload.

**Required arguments:**
- `-k` / `--kernel`: Path to compressed kernel image (`Image.lzma`)
- `-d` / `--dtbpack`: Path to the device tree blob pack (dtbpack)

**Optional arguments:**
- `-r` / `--initrd`: Path to initial ramdisk (initramfs)
- `-c` / `--cmdline`: Custom kernel command line

### Loading Sequence

The script sends components to pongoOS in this order:

1. **Set kernel command line:** Sends the cmdline string via USB control transfer
2. **Load initrd (if provided):** Sends size (packed as 32-bit integer), then bulk-transfers
   the ramdisk data (1MB timeout), then sends acknowledgment
3. **Load device tree blob:** Sends size, writes FDT data, sends "fdt\n" acknowledgment
4. **Load kernel image:** Sends size, bulk-transfers kernel data (1MB timeout)
5. **Trigger boot:** Sends "bootl\n" command to initiate Linux boot

The script uses USB control transfer command IDs:
- Command 1: Size specification
- Command 2: Data preparation
- Command 3: Command transmission
- Command 4: Session initialization/reset

Upon receiving "bootl", pongoOS calls `linux_prep_boot()` to prepare the environment, then
jumps to the kernel entry point.

### pongoOS Linux Support Status

The `linux_cmdline`, `fdt` and `bootl` commands are not present in every pongoOS build.
Verified against the PongoOS source and the binaries themselves (2026-10-23):

| pongoOS build | Version string | Linux commands | Linux path |
|---------------|----------------|----------------|------------|
| `boot/Pongo.bin` ([2.6.1 release](https://github.com/checkra1n/PongoOS/releases/tag/2.6.1) asset, 254032 bytes) | `PongoOS-2.6.1-742d92a0` | `linux_cmdline`, `fdt`, `ramdisk`, `bootl` | `bootl` |
| palera1n (`cdn.nickchan.lol/palera1n/artifacts/kpf/iOS15/Pongo.bin`) | `PongoOS-2.6.3-e98323f8` | none | `bootm` (m1n1) |
| HoolockLinux (`docs/binaries/Pongo.bin`, built from PongoOS `bb492b0`, 2025-02-22) | `PongoOS-2.6.3-bb492b00` | none | `bootm` (m1n1) |

- In 2.6.1, `shell_main()` (`src/shell/main.c`) calls `linux_commands_register()` before
  `command_init()` starts the shell loop (`command_main`), so the commands are always
  registered before any command is processed.
  `Bad command: linux_cmdline` therefore means the device runs a build without them.
- Commit [455eabb](https://github.com/checkra1n/PongoOS/commit/455eabb1bce5bb695ca3192294823849605f209e)
  (2024-09-14, `iOS15` branch) removed `src/modules/linux` and `scripts/load_linux.py`, with
  the message "Sandcastle never worked on pongoOS 2.6.x. Wash it away." The HoolockLinux build
  includes this commit; palera1n's build commit (`e98323f8`) is not public, but the binary
  lacks the commands as well. The removal is not in
  any tag: the 2.6.3 tag still has the commands, but builds from later `iOS15` commits also
  report `2.6.3-<commit>` (the Makefile hardcodes the prefix). The version number alone does
  not tell the two apart; the `Bad command:` reply does.
- `linux_prep_boot()` in 2.6.1 prints "This is only supported on iPhone 7 for now and works
  to a lesser extent on other A10 devices. Behavior on non-A10 devices is undefined!!"
  The `bootl` path is untested on A8X.
- HoolockLinux boots A7-A11 devices with an iOS15-branch pongoOS that loads
  [m1n1](https://github.com/HoolockLinux/m1n1), which then boots Linux: `palera1n -lp -k Pongo.bin`,
  then `/send m1n1-linux.bin` and `bootm` in `pongoterm`
  ([SETUP_pongoOS.md](https://github.com/HoolockLinux/docs/blob/HEAD/tutorials/SETUP_pongoOS.md)).
  Its A8X feature table lists the iPad Air 2 device tree, main display and buttons as
  upstream since Linux 6.13 ([features/A8.md](https://github.com/HoolockLinux/docs/blob/HEAD/features/A8.md)).
  This repository does not implement the m1n1 path yet.

### Device Tree: How Linux Gets Hardware Information

Linux requires a Flattened Device Tree Blob (FDT/DTB) to discover hardware. For iPad Air 2:

**Source of device tree:** The DTB is NOT from pongoOS or the Apple Device Tree. It must be
compiled separately from Linux-format `.dts`/`.dtsi` source files and passed to pongoOS as
the "dtbpack" argument. The dtbpack is a simple container format for one or more DTB files.

**Mainline kernel device tree status:**
- Device tree patches for A7-A11 Apple devices have been posted to the Linux kernel mailing
  list by Nick Chan (towinchenmi@gmail.com), based on work by Konrad Dybcio
- The patch series has gone through multiple revisions (v1 through v8+)
- The iPad Air 2 is identified as `apple,j81` (Wi-Fi) and `apple,j82` (Cellular)
- The SoC identifier is `apple,t7001` (A8X)
- Basic device tree support was merged starting with Linux 6.13 and expanded in 6.15

**What the device tree defines for t7001:**
- CPU: Triple-core ARM Typhoon (ARMv8-A), spin-table boot method
- Memory: Starting at 0x800000000, size filled by bootloader
- UART: Serial controller (for console output)
- AIC: Apple Interrupt Controller
- Pinctrl: GPIO controller
- Watchdog timer
- Simple framebuffer: Pre-initialized by iBoot, Linux uses it as-is
- Backlight: Display backlight control (added in Linux 6.15 cycle)
- CPU PMU: Performance monitoring (added in v8 patches)

**Peripheral addresses (from A8 device tree, t7001 similar):**
- UART: `0x20a0c0000`
- Watchdog: `0x20e027000`
- AIC: `0x20e100000`
- Pinctrl/GPIO: `0x20e300000`

### ARM64 Boot Protocol

pongoOS follows the standard ARM64 boot protocol when handing off to Linux:
- x0 register: Physical address of the FDT (device tree blob) in RAM
- x1, x2, x3: Reserved, set to zero
- MMU may be on or off (Linux handles both)
- The FDT must be aligned on a 64-byte boundary
- Linux verifies the FDT magic value (0xd00dfeed) at the address in x0

### Kernel Image Format

The Linux kernel is compiled as `Image` (raw binary) and then compressed to `Image.lzma`.
pongoOS decompresses the image in memory before jumping to it.

### initramfs / Ramdisk

An initramfs is essential for iPad Linux boot since there are no native Linux filesystem
drivers for Apple's NAND storage on A8X devices:
- The initramfs provides a minimal root filesystem in memory
- Typically contains BusyBox for basic shell utilities
- Can include networking tools for NFS root or USB networking
- postmarketOS packages can be used to build a complete initramfs
- The ramdisk approach means the entire userland runs from RAM

### Kernel Configuration Requirements

Based on existing A7-A11 Linux work, the kernel needs (at minimum):

```
# Architecture
CONFIG_ARCH_APPLE=y          # Apple SoC platform support
CONFIG_ARM64=y               # AArch64 architecture

# Boot
CONFIG_ARM64_VA_BITS_48=y    # 48-bit virtual addresses
CONFIG_ARM64_PAGE_SHIFT=14   # 16KB pages (Apple SoC standard)
CONFIG_CMDLINE_EXTEND=y      # Allow bootloader cmdline extension

# Interrupt controller
CONFIG_APPLE_AIC=y           # Apple Interrupt Controller driver

# Display
CONFIG_FB_SIMPLE=y           # Simple framebuffer support
# or CONFIG_DRM_SIMPLEDRM=y  # DRM simple display driver

# Serial/Console
CONFIG_SERIAL_SAMSUNG=y      # Apple UART is Samsung S3C compatible
CONFIG_SERIAL_SAMSUNG_CONSOLE=y

# Watchdog
CONFIG_APPLE_WATCHDOG=y      # Apple SoC watchdog

# GPIO
CONFIG_PINCTRL_APPLE_GPIO=y  # Apple GPIO/pinctrl driver

# Storage (ramdisk)
CONFIG_BLK_DEV_INITRD=y      # initramfs support
CONFIG_RD_LZMA=y             # LZMA decompression for ramdisk

# USB
CONFIG_USB_DWC2=y            # Synopsys DWC2 OTG controller
```

A kernel config file `config_16k` exists in the linux-apple-resources repository (formerly
SoMainline/linux-apple-resources, now maintained as HoolockLinux/docs), specifically targeting
16KB page size as used by Apple SoCs.

### Existing Kernel Work

| Project | Kernel version | Target | Status |
|---------|---------------|--------|--------|
| Konrad Dybcio | 5.18-rc1 | A7/A8/A8X | Booted on iPad Air 2, basic framebuffer |
| Project Sandcastle | ~5.4 (fork) | A10 (iPhone 7) | Full peripheral support |
| HoolockLinux | Recent mainline | A7-A11, T2 | Active documentation, boot guides |
| postmarketOS | 5.4.12 | A10 (iPhone 7) | Testing quality, WiFi+BT working |
| Mainline patches (Nick Chan) | 6.13+ | A7-A11 | Device trees merging into mainline |

Sources:
- https://github.com/checkra1n/PongoOS/blob/2.6.1/scripts/load_linux.py
- https://lore.kernel.org/lkml/20240925071939.6107-3-towinchenmi@gmail.com/T/
- https://patchew.org/linux/20240925071939.6107-1-towinchenmi@gmail.com/
- https://www.phoronix.com/news/Linux-6.13-Better-Apple-Pre-M1
- https://www.phoronix.com/news/Apple-Silicon-DT-3-Linux-6.15
- https://docs.kernel.org/arch/arm64/booting.html
- https://github.com/asdfugil/linux-apple-resources
- https://github.com/HoolockLinux/docs

---

## 4. Known Boot Issues and Debugging

### Common Failure Modes

**Exploit failure (checkm8 stage):**
- The heap feng shui is timing-sensitive; USB hubs and cable quality matter
- Achilles notes that "failing to send the overwrite (and thus exploit failure) is a common
  issue" on Linux hosts
- Workaround: retry, use a direct USB connection (no hub), try different USB ports
- A8X exploitation is generally reliable (more so than A11)

**`Bad command: linux_cmdline` (or `fdt`, `bootl`), device stays in pongoOS:**
- The running pongoOS has no Linux commands, typically a palera1n or HoolockLinux build
  (see "pongoOS Linux Support Status" above); every upload command is rejected
- Load `boot/Pongo.bin` (2.6.1) instead; `boot/load_linux.py` prints the build from the USB
  serial number (`SRTG:[PongoOS-...]`) and stops at the first rejected command

**pongoOS hangs after loading:**
- Can happen if the pongoOS binary is incompatible with the SoC
- Check that the correct pongoOS build is used for A8X
- Use `-S` flag in Achilles to enable serial output for debugging

**Kernel panic during early boot:**
- Incorrect device tree (wrong SoC compatible string, wrong peripheral addresses)
- Missing kernel config options (AIC driver, page size mismatch)
- Memory layout conflicts (kernel loaded at wrong address)
- 4KB vs 16KB page size mismatch (Apple SoCs use 16KB pages; kernel must be built with
  CONFIG_ARM64_PAGE_SHIFT=14)

**No display output:**
- The simple framebuffer requires iBoot to have initialized the display before pongoOS loads
- If the display pipeline was not set up by iBoot, simplefb will have no backing memory
- The framebuffer address and resolution must match what iBoot configured

**Filesystem mount failure:**
- If the initramfs is not provided or is corrupt, the kernel panics at "unable to mount
  root fs"
- This was the state of Konrad Dybcio's initial 2022 demonstration (basic boot but no rootfs)

### UART/Serial Output

Serial output is the primary debugging mechanism for early boot:

**Hardware UART:** Apple SoCs include a Samsung S3C-compatible UART controller. Physical
serial access requires hardware modification (soldering to test pads on the logic board).
The serial console operates at 115200 baud by default.

**USB serial via pongoOS:** pongoOS provides a USB serial console via `pongoterm`. Once the
Linux kernel takes over USB, this connection is lost unless the kernel is configured with
USB gadget serial support.

**Enabling serial:** The Achilles tool's `-S` flag enables serial output from pongoOS. For
the Linux kernel, add `earlycon` to the kernel command line and ensure the UART driver is
built in (not as a module).

**Serial Wire Debug (SWD):** An alternative debug interface available on Apple SoCs when the
CPFM (chip fuse mode) is below 0x01 or the device is "demoted." Not available on production
devices without exploit-assisted demotion.

### Memory Layout Considerations

Apple A8X memory layout:
- DRAM starts at physical address 0x800000000 (above 32-bit address space)
- 2GB total RAM (two 1GB Elpida F8164A3MD packages)
- The ARM IO region (peripheral MMIO) is in a separate address range (0x20xxxxxxxxx)
- pongoOS manages memory placement of the kernel, device tree, and initramfs
- The kernel must not overlap with pongoOS's own memory or reserved regions

The device tree's memory node is filled by the bootloader with the actual DRAM size and
layout. The `/chosen` node contains the kernel command line and initramfs location.

### Complete Boot Sequence Summary

```
1. User connects iPad Air 2 to host computer via USB (Lightning cable)
2. User enters DFU mode (button combination: Home + Power, then release Power)
3. Host runs: achilles -p -S                    # Exploit + load pongoOS + serial
4. pongoOS boots, initializes USB, presents shell
5. Host runs: python3 load_linux.py \
     -k Image.lzma \                            # Compressed kernel
     -d dtbpack \                                # Device tree for t7001/iPad Air 2
     -r initramfs.cpio.lzma \                    # Root filesystem
     -c "console=tty0 earlycon root=/dev/ram0"   # Kernel cmdline
6. pongoOS receives files, places them in memory
7. pongoOS calls linux_prep_boot(), sets x0 = FDT address
8. pongoOS jumps to kernel entry point
9. Linux kernel starts, parses FDT, initializes AIC, UART, framebuffer
10. Kernel mounts initramfs as root filesystem
11. init process starts (BusyBox or systemd from initramfs)
12. User can interact via USB networking (if configured) or display+touch (if drivers work)
```

Time from DFU mode to Linux shell: approximately 15-30 seconds.

Sources:
- https://github.com/alfiecg24/Achilles
- https://github.com/hmk3r/iphone-5s-linux-howto
- https://www.embeddedideation.com/2016/04/06/enabling-serial-io-on-ios-devices/
- https://theapplewiki.com/wiki/Serial_Wire_Debug
- https://hackaday.com/2022/06/12/boot-mainline-linux-on-apple-a7-a8-and-a8x-devices/
