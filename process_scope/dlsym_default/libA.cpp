#include "dso_common.hpp"
#include "process_logger.hpp"

extern "C" void libA_entry() {
    // Use dlsym to find get_process_logger at runtime
    get_logger_via_dlsym().log("libA");
}
