#include "core_api.hpp"
#include "process_logger.hpp"

// THE singleton instance - lives in libprocess_core.so
static ProcessLogger g_logger("core_shared_lib");

ProcessLogger& get_process_logger() {
    return g_logger;
}
