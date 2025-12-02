#include "thread_logger.hpp"
#include <thread>
#include <vector>

void worker(int id) {
    get_thread_logger().log(("worker " + std::to_string(id)).c_str());
}

int main() {
    std::cout << "=== Thread Scope Basic Demo ===\n\n";

    get_thread_logger().log("main");

    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(worker, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "\n=== Expected Result ===\n";
    std::cout << "Each thread has its own ThreadLogger (different addresses)\n";

    return 0;
}
