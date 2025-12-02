#include "process_logger.hpp"
#include <iostream>

// THE singleton instance - lives in main executable
static ProcessLogger g_logger("main_owner");

// Export this function so DSOs can find it at runtime
extern "C" ProcessLogger& get_process_logger() {
    return g_logger;
}

// Declare plugin entry points
extern "C" void libA_entry();
extern "C" void libB_entry();
extern "C" void libC_entry();

int main() {
    std::cout << "=== Process Scope: main_owner Demo ===\n\n";

    std::cout << "[main] calling logger directly:\n";
    get_process_logger().log("main");

    std::cout << "\n[main] calling through DSOs:\n";
    libA_entry();
    libB_entry();
    libC_entry();

    std::cout << "\n=== Key Insight ===\n";
    std::cout << "Singleton defined in main executable\n";
    std::cout << "DSOs find it via -Wl,--export-dynamic\n";
    std::cout << "(All addresses above should be identical)\n";

    return 0;
}
