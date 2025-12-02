#include <iostream>
#include <sys/file.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstdlib>
#include <cerrno>
#include <cstring>

constexpr const char* LOCK_FILE = "/tmp/os_scope_singleton.lock";

int main() {
    std::cout << "=== OS Scope: Machine-Level Singleton Demo ===\n\n";

    // 1. Open or create lock file
    int fd = open(LOCK_FILE, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        std::cerr << "Failed to open lock file: " << std::strerror(errno) << "\n";
        return 1;
    }

    std::cout << "[" << getpid() << "] Attempting to acquire exclusive lock...\n";

    // 2. Try to acquire exclusive lock (non-blocking)
    if (flock(fd, LOCK_EX | LOCK_NB) < 0) {
        if (errno == EWOULDBLOCK) {
            std::cerr << "[" << getpid() << "] Another instance is already running!\n";
        } else {
            std::cerr << "[" << getpid() << "] flock failed: " << std::strerror(errno) << "\n";
        }
        close(fd);
        return 1;
    }

    // 3. Lock acquired - we are the singleton
    std::cout << "[" << getpid() << "] Lock acquired! This is the singleton instance.\n";
    std::cout << "[" << getpid() << "] Lock file: " << LOCK_FILE << "\n\n";

    std::cout << "=== Key Insight ===\n";
    std::cout << "flock() creates an advisory lock on the file descriptor.\n";
    std::cout << "Only ONE process on this machine can hold LOCK_EX at a time.\n";
    std::cout << "The lock is automatically released when fd is closed or process exits.\n\n";

    std::cout << "Press Enter to release lock and exit...\n";
    std::cin.get();

    // 4. Lock is automatically released when fd is closed
    close(fd);
    std::cout << "[" << getpid() << "] Lock released. Daemon exiting.\n";

    return 0;
}
