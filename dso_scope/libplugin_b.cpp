#include "logger.hpp"

// Export this function so main can call it
extern "C" __attribute__((visibility("default"))) void plugin_b_entry() {
    std::cout << "[plugin_b] logger @" << &get_logger() << "\n";
}
