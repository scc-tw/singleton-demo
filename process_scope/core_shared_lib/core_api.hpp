#pragma once

struct ProcessLogger;

// Returns the process-wide singleton logger
// Defined in libprocess_core.so
ProcessLogger& get_process_logger();
