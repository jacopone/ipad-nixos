#!/usr/bin/env python3
# load_linux.py — Upload Linux kernel/dtb/initrd to pongoOS via USB
#
# Based on: https://github.com/checkra1n/PongoOS/blob/2.6.1/scripts/load_linux.py
# (removed upstream in commit 455eabb, 2024-09-14)
# License: MIT (checkra1n project)
#
# Usage: sudo python3 load_linux.py -k Image.lzma -d dtbpack -r initramfs.cpio.lzma -c "cmdline"
#
# Requires: pyusb (pip install pyusb)
# The pongoOS USB device presents as 05ac:4141 (Apple DFU/recovery variant)
#
# Unlike the upstream script, every shell command is followed by a read of the
# pongoOS stdout buffer, so a rejected command aborts with the device's own
# error message instead of being ignored. The USB control requests used here
# are handled in PongoOS src/shell/usbloader.c (ep0_device_request).

import usb.core
import usb.util
import struct
import sys
import argparse
import time

# usbloader.c accepts stdin writes of at most 512 bytes; command_main() reads
# them with fgets(command_buffer, 512, stdin).
PONGO_STDIN_MAX = 511
# LINUX_DTREE_SIZE in PongoOS src/kernel/pongo.h; fdt_cmd() copies the upload
# into a buffer of this size without a bounds check.
PONGO_FDT_MAX = 262144

# Lines pongoOS prints when a Linux boot command fails (PongoOS 2.6.1
# src/shell/command.c, src/shell/linux.c, src/modules/linux/linux.c).
PONGO_ERRORS = (
    "Bad command:",
    "please upload",
    "linux_cmdline usage:",
    "greater than LINUX_CMDLINE_SIZE",
    "linux boot not prepared",
    "Device tree for",  # "Device tree for <target> not found."
    "failed to apply overlay",
    "Cannot update chosen node",
)

NO_LINUX_SUPPORT = """
The pongoOS running on the device does not provide the Linux boot commands
(linux_cmdline, fdt, bootl). They exist in pongoOS releases up to tag 2.6.3,
such as boot/Pongo.bin (PongoOS-2.6.1-742d92a0). Later builds, including the
ones shipped by palera1n and HoolockLinux, removed them and boot Linux
through m1n1 (`bootm`) instead; they still report version 2.6.3-<commit>.
Load boot/Pongo.bin. See README.md, "Troubleshooting".
"""

parser = argparse.ArgumentParser(description='A little Linux kernel/initrd uploader for pongoOS.')

parser.add_argument('-k', '--kernel', dest='kernel', help='path to kernel image')
parser.add_argument('-d', '--dtbpack', dest='dtbpack', help='path to dtbpack')
parser.add_argument('-r', '--initrd', dest='initrd', help='path to initial ramdisk')
parser.add_argument('-c', '--cmdline', dest='cmdline', help='custom kernel command line')

args = parser.parse_args()


def fail(message, detail=None):
    sys.stdout.flush()
    if detail:
        print(detail, file=sys.stderr)
    print(f"error: {message}", file=sys.stderr)
    exit(1)


def read_stdout(dev):
    return bytes(dev.ctrl_transfer(0xa1, 1, 0, 0, 0x1000)).decode(errors="replace")


def issue_command(dev, command):
    """Run a pongoOS shell command and return its output, aborting on a known error."""
    line = command + "\n"
    if len(line) > PONGO_STDIN_MAX:
        fail(f"pongoOS command is {len(line)} bytes, the limit is {PONGO_STDIN_MAX}: {command[:60]}...")
    # wValue=0: the stdin write stalls until pongoOS has finished the command.
    dev.ctrl_transfer(0x21, 4, 0, 0, 0)
    dev.ctrl_transfer(0x21, 3, 0, 0, line)
    output = read_stdout(dev)
    for out_line in output.replace("\r", "\n").splitlines():
        if out_line.strip() and out_line.strip() != "pongoOS>":
            print(f"    pongoOS: {out_line.rstrip()}")
    for error in PONGO_ERRORS:
        if error in output:
            detail = NO_LINUX_SUPPORT if error == "Bad command:" else None
            fail(f"pongoOS rejected `{command.split()[0]}`", detail)
    return output


if args.kernel is None:
    print(f"error: No kernel specified! Run `{sys.argv[0]} --help` for usage.")
    exit(1)

if args.dtbpack is None:
    print(f"error: No dtbpack specified! Run `{sys.argv[0]} --help` for usage.")
    exit(1)

kernel = open(args.kernel, "rb").read()
fdt = open(args.dtbpack, "rb").read()

if len(fdt) > PONGO_FDT_MAX:
    fail(f"dtbpack is {len(fdt)} bytes, pongoOS accepts at most {PONGO_FDT_MAX}")

dev = usb.core.find(idVendor=0x05ac, idProduct=0x4141)
if dev is None:
    print("Waiting for device...")

    while dev is None:
        dev = usb.core.find(idVendor=0x05ac, idProduct=0x4141)
        if dev is not None:
            dev.set_configuration()
            break
        time.sleep(2)
else:
    dev.set_configuration()

# The serial number carries the build: "CPID:7001 BDID:.. ECID:... SRTG:[PongoOS-<version>]"
try:
    print(f"Device: {usb.util.get_string(dev, dev.iSerialNumber)}")
except (usb.core.USBError, ValueError) as e:
    print(f"Device: serial number unreadable ({e})")

# Drain the boot banner, then check that the Linux commands exist before
# spending time on the uploads. With no pending upload, `fdt` only prints
# "please upload a fdt before issuing this command".
read_stdout(dev)
dev.ctrl_transfer(0x21, 2, 0, 0, 0)
dev.ctrl_transfer(0x21, 4, 0, 0, 0)
dev.ctrl_transfer(0x21, 3, 0, 0, "fdt\n")
probe = read_stdout(dev)
if "Bad command:" in probe:
    fail("pongoOS has no `fdt` command", NO_LINUX_SUPPORT)

if args.cmdline is not None:
    issue_command(dev, f"linux_cmdline {args.cmdline}")

if args.initrd is not None:
    print("Loading initial ramdisk...")
    initrd = open(args.initrd, "rb").read()
    initrd_size = len(initrd)
    dev.ctrl_transfer(0x21, 2, 0, 0, 0)
    dev.ctrl_transfer(0x21, 1, 0, 0, struct.pack('I', initrd_size))

    dev.write(2, initrd, 1000000)
    issue_command(dev, "ramdisk")
    print("Initial ramdisk loaded successfully.")

print("Loading device tree...")
dev.ctrl_transfer(0x21, 2, 0, 0, 0)
dev.ctrl_transfer(0x21, 1, 0, 0, 0)
dev.write(2, fdt)

issue_command(dev, "fdt")
print("Device tree loaded successfully.")

print("Loading kernel...")
kernel_size = len(kernel)
dev.ctrl_transfer(0x21, 2, 0, 0, 0)
dev.ctrl_transfer(0x21, 1, 0, 0, struct.pack('I', kernel_size))

dev.write(2, kernel, 1000000)
print("Kernel uploaded.")

print("Booting...")
try:
    issue_command(dev, "bootl")
except usb.core.USBError as e:
    # pongoOS drops off the bus when it hands over to the kernel
    print(f"Device disconnected ({e}); pongoOS is most likely handing over to Linux.")
else:
    print("pongoOS accepted `bootl` and is still connected.")
    print("If the screen stays on pongoOS, Linux did not start: check the serial console.")
