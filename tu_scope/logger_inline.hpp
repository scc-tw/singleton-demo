#pragma once
#include "logger.hpp"

// C++17: inline variable guarantees a single instance across the entire binary
inline Logger g_logger_inline;

inline Logger& get_logger_inline() {
    return g_logger_inline;
}
