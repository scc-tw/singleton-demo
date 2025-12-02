#include "shm_logger.hpp"
#include "process_logger.hpp"

extern "C" void libC_entry() {
    get_shm_logger().log("libC");
}
