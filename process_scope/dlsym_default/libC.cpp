#include "dso_common.hpp"
#include "process_logger.hpp"

extern "C" void libC_entry() {
    get_logger_via_dlsym().log("libC");
}
