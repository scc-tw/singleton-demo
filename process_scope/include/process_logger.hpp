#pragma once
#include <iostream>

struct ProcessLogger {
    explicit ProcessLogger(const char* tag) : tag_(tag) {
        std::cout << "ProcessLogger[" << tag_ << "] ctor @" << this << "\n";
    }

    void log(const char* who) const {
        std::cout << "[" << who << "] logger @" << this
                  << " (tag=" << tag_ << ")\n";
    }

private:
    const char* tag_;
};
