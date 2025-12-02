#include "process_logger.hpp"

// Declaration only - definition is in main executable
// Resolved at runtime via --export-dynamic
extern "C" ProcessLogger& get_process_logger();

extern "C" void libA_entry() {
    get_process_logger().log("libA");
}
