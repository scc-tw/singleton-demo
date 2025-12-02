#include "logger_static.hpp"
#include "logger_inline.hpp"

void user_a_report() {
    std::cout << "[user_a] static:  " << &get_logger_static() << "\n";
    std::cout << "[user_a] inline:  " << &get_logger_inline() << "\n";
}
