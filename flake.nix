{
  description = "iPad NixOS - Linux on iPad via checkm8/pongoOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv = {
      url = "github:cachix/devenv";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, devenv, ... }@inputs:
    let
      buildSystem = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${buildSystem};

      # Cross-compilation: build on x86_64, target aarch64 (iPad ARM64)
      # glibc variant — used for the kernel build (buildLinux handles cross internally)
      pkgsCross = import nixpkgs {
        localSystem.system = buildSystem;
        crossSystem.system = "aarch64-linux";
      };

      # musl variant — for the initramfs.
      # musl gives fully self-contained binaries: no glibc version skew,
      # simpler static linking.  aarch64-unknown-linux-musl is the triple.
      pkgsCrossMusl = import nixpkgs {
        localSystem.system = buildSystem;
        crossSystem = {
          config = "aarch64-unknown-linux-musl";
          # 16KB page size is a kernel concern, not a userspace concern.
          # musl and busybox do not need a special page-size override here.
        };
      };
    in
    {
      # Dev shell (x86_64 tools for RE, flashing, serial, etc.)
      devShells.${buildSystem}.default = devenv.lib.mkShell {
        inherit inputs pkgs;
        modules = [ ./devenv.nix ];
      };

      # Cross-compiled packages for iPad (aarch64, 16KB pages)
      packages.${buildSystem} = {
        # checkm8 exploit tool for the host (A5-A11, including 32-bit A6/A6X)
        # Build: nix build .#gaster ; run: sudo result/bin/gaster pwn
        gaster = pkgs.callPackage ./boot/gaster.nix {};

        # Linux kernel for iPad Air 2 (A8X)
        kernel = pkgsCross.callPackage ./kernel {};

        # Minimal initramfs — entire root filesystem in RAM
        # Build: nix build .#initramfs
        # Output: result/initrd  (symlink to result/initrd.zst)
        initramfs = pkgsCrossMusl.callPackage ./nixos/initramfs.nix {};
      };
    };
}
