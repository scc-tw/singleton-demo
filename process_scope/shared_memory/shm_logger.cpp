#include "shm_logger.hpp"
#include "process_logger.hpp"

#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <mutex>
#include <iostream>
#include <cstring>
#include <new>  // placement new

static const char* SHM_NAME = "/process_scope_logger";

// Process-local state
static ShmBlock* g_block = nullptr;
static std::once_flag g_init_flag;

static void init_shm_block() {
    // Open or create shared memory object
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        perror("shm_open failed");
        std::abort();
    }

    // Set size (only effective on first creation)
    if (ftruncate(fd, sizeof(ShmBlock)) < 0) {
        perror("ftruncate failed");
        close(fd);
        std::abort();
    }

    // Map into our address space
    void* addr = mmap(nullptr, sizeof(ShmBlock),
                      PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);  // fd can be closed after mmap

    if (addr == MAP_FAILED) {
        perror("mmap failed");
        std::abort();
    }

    g_block = static_cast<ShmBlock*>(addr);
    std::cout << "[shm] mapped @" << g_block << "\n";

    // One-time initialization using atomic flag
    // Note: This is safe within a single process (multiple DSOs)
    // For cross-process, we'd need a process-robust mutex
    bool expected = false;
    if (g_block->initialized.compare_exchange_strong(expected, true)) {
        // We are the first to initialize
        std::cout << "[shm] initializing ProcessLogger in shared memory\n";
        new (g_block->storage) ProcessLogger("shared_memory");
    } else {
        std::cout << "[shm] ProcessLogger already initialized\n";
    }
}

ProcessLogger& get_shm_logger() {
    std::call_once(g_init_flag, init_shm_block);
    return *reinterpret_cast<ProcessLogger*>(g_block->storage);
}

void cleanup_shm_logger() {
    if (g_block) {
        munmap(g_block, sizeof(ShmBlock));
        g_block = nullptr;
    }
    // Optionally unlink (remove) the shared memory object
    // Only the last process should do this
    // shm_unlink(SHM_NAME);
}
