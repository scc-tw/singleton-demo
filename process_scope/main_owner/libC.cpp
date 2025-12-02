#include "process_logger.hpp"

extern "C" ProcessLogger& get_process_logger();

extern "C" void libC_entry() {
    get_process_logger().log("libC");
}
