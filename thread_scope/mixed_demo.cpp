#include "thread_logger.hpp"
#include "libworker.hpp"
#include <thread>
#include <iostream>

void test_cross_dso() {
    std::cout << "--- Same thread, different DSOs ---\n";
    get_thread_logger().log("main_exe");
    call_logger_in_lib("lib_worker");
    std::cout << "(Should be SAME address - per-thread global)\n\n";
}

int main() {
    std::cout << "=== Thread Scope Mixed Demo (Cross-DSO) ===\n\n";

    std::cout << "[Main Thread]\n";
    test_cross_dso();

    std::thread t([] {
        std::cout << "[Worker Thread]\n";
        test_cross_dso();
    });
    t.join();

    std::cout << "=== Key Insight ===\n";
    std::cout << "inline thread_local: same address within same thread across DSOs\n";
    std::cout << "This differs from dso_scope where inline var is per-DSO\n";

    return 0;
}
