#include "logger_static.hpp"
#include "logger_inline.hpp"

void user_b_report() {
    std::cout << "[user_b] static:  " << &get_logger_static() << "\n";
    std::cout << "[user_b] inline:  " << &get_logger_inline() << "\n";
}
