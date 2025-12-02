#pragma once
#include <iostream>

struct Logger {
    Logger() { std::cout << "Logger ctor @" << this << "\n"; }
    void log(const char* msg) const {
        std::cout << "[" << msg << "] @" << this << "\n";
    }
};
