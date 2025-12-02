#pragma once
#include <atomic>
#include <cstddef>

struct ProcessLogger;

// Shared memory block layout
// This structure lives in kernel-managed shared memory
struct ShmBlock {
    std::atomic<bool> initialized{false};  // Atomic flag for one-time init
    alignas(64) char storage[256];  // Storage for ProcessLogger (aligned)
};

// Get the singleton logger from shared memory
// First caller creates and initializes it, subsequent callers get the same instance
ProcessLogger& get_shm_logger();

// Cleanup shared memory (call once at program exit)
void cleanup_shm_logger();
