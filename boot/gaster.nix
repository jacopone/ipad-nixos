# Nix derivation for gaster — checkm8 bootrom exploit tool
#
# gaster exploits the checkm8 vulnerability (CVE-2019-8900) in Apple A5-A11
# SoCs via USB DFU mode. It places the device in "pwned DFU" state, allowing
# unsigned code (pongoOS) to be loaded.
#
# Usage: sudo gaster pwn

{ lib
, stdenv
, fetchFromGitHub
, libusb1
, openssl
, xxd
}:

stdenv.mkDerivation {
  pname = "gaster";
  version = "unstable-2023-02-02";

  src = fetchFromGitHub {
    owner = "0x7ff";
    repo = "gaster";
    rev = "7fffffff38a1bed1cdc1c5bae0df70f14395129b";
    hash = "sha256-TZu4IoV7Zu30mEW+ctPtpYjhF8iRTjioz8HAKXKcRdo=";
  };

  nativeBuildInputs = [ xxd ];
  buildInputs = [ libusb1 openssl ];

  buildPhase = ''
    runHook preBuild

    # Generate payload headers from binary blobs
    for f in payload_A9.bin payload_notA9.bin payload_notA9_armv7.bin \
             payload_handle_checkm8_request.bin payload_handle_checkm8_request_armv7.bin; do
      xxd -iC "$f" "''${f%.bin}.h"
    done

    # Build with libusb support (Linux)
    $CC -Wall -Wextra -Wpedantic -DHAVE_LIBUSB \
      gaster.c lzfse.c \
      -o gaster \
      -lusb-1.0 -lcrypto -Os

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    install -Dm755 gaster $out/bin/gaster
    runHook postInstall
  '';

  meta = with lib; {
    description = "checkm8 (CVE-2019-8900) bootrom exploit tool for Apple A5-A11";
    homepage = "https://github.com/0x7ff/gaster";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
