#include "core_api.hpp"
#include "process_logger.hpp"

extern "C" void libA_entry() {
    get_process_logger().log("libA");
}
