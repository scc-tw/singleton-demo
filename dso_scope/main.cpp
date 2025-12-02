#include "logger.hpp"
#include <iostream>

extern "C" void plugin_a_entry();
extern "C" void plugin_b_entry();

int main() {
    std::cout << "=== DSO Scope Singleton Demo ===\n\n";

    std::cout << "[main] logger @" << &get_logger() << "\n\n";

    plugin_a_entry();
    plugin_b_entry();

    std::cout << "\n=== Expected Result ===\n";
    std::cout << "main, plugin_a, plugin_b all have DIFFERENT addresses\n";
    std::cout << "This demonstrates per-DSO scope for inline variables\n";

    return 0;
}
