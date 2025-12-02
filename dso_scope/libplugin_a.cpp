#include "logger.hpp"

// Export this function so main can call it
extern "C" __attribute__((visibility("default"))) void plugin_a_entry() {
    std::cout << "[plugin_a] logger @" << &get_logger() << "\n";
}
