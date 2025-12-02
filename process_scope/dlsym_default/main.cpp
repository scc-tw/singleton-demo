#include "process_logger.hpp"
#include <iostream>

// THE singleton instance - lives in main executable
static ProcessLogger g_logger("dlsym_default");

// Export this function so DSOs can find it via dlsym(RTLD_DEFAULT, ...)
extern "C" ProcessLogger& get_process_logger() {
    return g_logger;
}

// Declare plugin entry points
extern "C" void libA_entry();
extern "C" void libB_entry();
extern "C" void libC_entry();

int main() {
    std::cout << "=== Process Scope: dlsym_default Demo ===\n\n";

    std::cout << "[main] calling logger directly:\n";
    get_process_logger().log("main");

    std::cout << "\n[main] calling through DSOs (using dlsym):\n";
    libA_entry();
    libB_entry();
    libC_entry();

    std::cout << "\n=== Key Insight ===\n";
    std::cout << "DSOs use dlsym(RTLD_DEFAULT, \"get_process_logger\")\n";
    std::cout << "This is true late binding - no link-time resolution needed\n";
    std::cout << "(All addresses above should be identical)\n";

    return 0;
}
