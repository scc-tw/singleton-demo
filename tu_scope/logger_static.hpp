#pragma once
#include "logger.hpp"

// WARNING: Each TU that includes this header gets its own g_logger_static
// This is a common pitfall when using static in headers
static Logger g_logger_static;

static Logger& get_logger_static() {
    return g_logger_static;
}
