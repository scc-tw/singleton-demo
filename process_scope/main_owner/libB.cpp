#include "process_logger.hpp"

extern "C" ProcessLogger& get_process_logger();

extern "C" void libB_entry() {
    get_process_logger().log("libB");
}
