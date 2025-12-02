#include "shm_logger.hpp"
#include "process_logger.hpp"
#include <iostream>
#include <cstdlib>

// Declare plugin entry points
extern "C" void libA_entry();
extern "C" void libB_entry();
extern "C" void libC_entry();

int main() {
    std::cout << "=== Process Scope: shared_memory Demo ===\n\n";

    std::cout << "[main] getting logger from shared memory:\n";
    get_shm_logger().log("main");

    std::cout << "\n[main] calling through DSOs:\n";
    libA_entry();
    libB_entry();
    libC_entry();

    std::cout << "\n=== Key Insight ===\n";
    std::cout << "ProcessLogger lives in kernel-managed shared memory\n";
    std::cout << "All DSOs mmap the same shm object -> same physical memory\n";
    std::cout << "This technique can be extended to cross-process (os_scope)\n";

    // Cleanup
    cleanup_shm_logger();

    return 0;
}
