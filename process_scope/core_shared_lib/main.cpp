#include "core_api.hpp"
#include "process_logger.hpp"
#include <iostream>

// Declare plugin entry points
extern "C" void libA_entry();
extern "C" void libB_entry();
extern "C" void libC_entry();

int main() {
    std::cout << "=== Process Scope: core_shared_lib Demo ===\n\n";

    std::cout << "[main] calling logger directly:\n";
    get_process_logger().log("main");

    std::cout << "\n[main] calling through DSOs:\n";
    libA_entry();
    libB_entry();
    libC_entry();

    std::cout << "\n=== Key Insight ===\n";
    std::cout << "All DSOs link to libprocess_core.so\n";
    std::cout << "Therefore all share the SAME ProcessLogger instance\n";
    std::cout << "(All addresses above should be identical)\n";

    return 0;
}
