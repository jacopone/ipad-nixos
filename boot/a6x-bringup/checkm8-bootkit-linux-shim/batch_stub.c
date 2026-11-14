/* Stub replacing batch.m (Objective-C, macOS-only) for a Linux build.
 * We only need the "boot" verb tonight; "batch" is unused but main.c
 * references these symbols unconditionally, so the linker needs them. */
#include "batch.h"
#include <stdio.h>

int batch_init(void *input, size_t size, void **ctx) {
    (void)input; (void)size; (void)ctx;
    fprintf(stderr, "batch mode not built on this platform (Linux stub)\n");
    return -1;
}
int batch_write(void *ctx, const char *path) { (void)ctx; (void)path; return -1; }
void batch_quiesce(void **ctx) { (void)ctx; }
int batch_get_count(void *ctx) { (void)ctx; return 0; }
int batch_get_kbag(void *ctx, int idx, uint8_t *kbag, size_t *len) {
    (void)ctx; (void)idx; (void)kbag; (void)len; return -1;
}
int batch_set_key(void *ctx, int idx, uint8_t *kbag, size_t len) {
    (void)ctx; (void)idx; (void)kbag; (void)len; return -1;
}
