#include "dso_common.hpp"
#include <dlfcn.h>
#include <stdexcept>
#include <iostream>

// Cache the resolved function pointer
static GetLoggerFn g_cached_fn = nullptr;

GetLoggerFn resolve_get_logger() {
    if (g_cached_fn) {
        return g_cached_fn;
    }

    // RTLD_DEFAULT: search all loaded shared objects
    // This will find get_process_logger defined in main (with --export-dynamic)
    void* sym = dlsym(RTLD_DEFAULT, "get_process_logger");

    if (!sym) {
        const char* err = dlerror();
        throw std::runtime_error(
            std::string("dlsym failed: ") + (err ? err : "unknown error"));
    }

    std::cout << "[dlsym] resolved get_process_logger @" << sym << "\n";
    g_cached_fn = reinterpret_cast<GetLoggerFn>(sym);
    return g_cached_fn;
}

ProcessLogger& get_logger_via_dlsym() {
    return resolve_get_logger()();
}
