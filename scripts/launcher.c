/**
 * Whisk Desktop — Native macOS launcher.
 * Finds the launcher.sh script in the same directory and executes it.
 * This Mach-O binary is required by macOS Launch Services (the `open` command).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libgen.h>
#include <mach-o/dyld.h>

int main(int argc, char *argv[]) {
    char exe_path[4096];
    uint32_t size = sizeof(exe_path);

    if (_NSGetExecutablePath(exe_path, &size) != 0) {
        fprintf(stderr, "Error: Could not determine executable path\n");
        return 1;
    }

    /* Resolve to real path */
    char *real = realpath(exe_path, NULL);
    if (!real) {
        fprintf(stderr, "Error: Could not resolve path\n");
        return 1;
    }

    /* Build path to launcher.sh in same directory */
    char *dir = dirname(real);
    char script_path[4096];
    snprintf(script_path, sizeof(script_path), "%s/launcher.sh", dir);
    free(real);

    /* Execute the shell launcher */
    execl("/bin/bash", "bash", script_path, NULL);

    /* If we get here, execl failed */
    perror("Failed to launch");
    return 1;
}
