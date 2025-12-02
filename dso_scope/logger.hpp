#pragma once
#include <iostream>

struct Logger {
    Logger() { std::cout << "Logger ctor @" << this << "\n"; }
    void log(const char* msg) { std::cout << "[" << msg << "] @" << this << "\n"; }
};

// Even with inline, each DSO gets its own copy
inline Logger g_logger;

inline Logger& get_logger() { return g_logger; }
