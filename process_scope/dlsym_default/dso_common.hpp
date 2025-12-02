#pragma once

struct ProcessLogger;

// Function pointer type for get_process_logger()
using GetLoggerFn = ProcessLogger& (*)();

// Resolve get_process_logger at runtime using dlsym(RTLD_DEFAULT, ...)
// This allows DSOs to find symbols without link-time resolution
GetLoggerFn resolve_get_logger();

// Convenience wrapper
ProcessLogger& get_logger_via_dlsym();
