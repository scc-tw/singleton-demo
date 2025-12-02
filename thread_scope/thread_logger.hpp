#pragma once
#include <iostream>
#include <thread>

struct ThreadLogger {
    ThreadLogger() {
        std::cout << "ThreadLogger ctor @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }

    void log(const char* context) {
        std::cout << "[" << context << "] @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }
};

// C++17: inline thread_local - per-thread, but shared across DSOs
inline thread_local ThreadLogger g_thread_logger;

inline ThreadLogger& get_thread_logger() {
    return g_thread_logger;
}
