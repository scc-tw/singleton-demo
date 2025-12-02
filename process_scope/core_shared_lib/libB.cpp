#include "core_api.hpp"
#include "process_logger.hpp"

extern "C" void libB_entry() {
    get_process_logger().log("libB");
}
