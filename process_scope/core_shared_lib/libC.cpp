#include "core_api.hpp"
#include "process_logger.hpp"

extern "C" void libC_entry() {
    get_process_logger().log("libC");
}
