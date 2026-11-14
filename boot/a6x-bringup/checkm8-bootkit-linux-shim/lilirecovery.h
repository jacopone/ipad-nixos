/* Shim so the portable checkm8_bootkit sources (which #include <lilirecovery.h>,
 * NyanSatan's IOKit-only fork) link against the real, Linux-portable
 * libimobiledevice/libirecovery from nixpkgs instead. */
#include <libirecovery.h>
