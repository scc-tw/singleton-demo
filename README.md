# C++ Singleton Scope Tutorial Report

Gamma slides: https://gamma.app/docs/C-Singleton-Scope-Tutorial-Report-2mqxzk0kxt5lx2d

## 1. Overview

### What is the Singleton Pattern?

The Singleton pattern ensures a class has only **one instance** and provides a global point of access to it. In C++, this seemingly simple pattern becomes complex when considering:

- Multiple translation units (TUs)
- Dynamic shared objects (DSOs / .so files)
- Multi-threading
- Multiple processes
- Machine-wide uniqueness

### Why Does Scope Matter?

In C++, a "singleton" can have different meanings depending on the scope:

| Scope | Meaning |
|-------|---------|
| Translation Unit | One instance per .cpp file |
| Binary | One instance per executable |
| DSO | One instance per shared library |
| Thread | One instance per thread |
| Process | One instance per process (across all DSOs) |
| Machine | One instance per machine (across all processes) |

### The 5 Scope Levels

This tutorial covers five progressively complex scope levels:

1. **tu_scope** — Translation Unit: `static` vs `inline`
2. **dso_scope** — Dynamic Shared Object: Symbol visibility
3. **thread_scope** — Thread-Local Storage: `thread_local`
4. **process_scope** — Process-wide: 4 practical patterns
5. **os_scope** — Machine-wide: Kernel locks

## 2. Level 1: Translation Unit Scope

### Problem

Why `static` in header fails to create a true singleton

### Mechanism

C++17 `inline` variable guarantees a single instance across the entire binary, regardless of how many TUs include the header.

### Key Code

**The Pitfall: `static` creates per-TU copies**

```cpp
// logger_static.hpp - WARNING: Each TU gets its own copy!
static Logger g_logger_static;

static Logger& get_logger_static() {
    return g_logger_static;
}
```

**The Solution: `inline` ensures one instance (C++17)**

```cpp
// logger_inline.hpp - Single instance across entire binary
inline Logger g_logger_inline;

inline Logger& get_logger_inline() {
    return g_logger_inline;
}
```

### Expected Output

```
[user_a] static:  0x404100
[user_a] inline:  0x404180
[user_b] static:  0x404120   <- DIFFERENT! (per-TU copy)
[user_b] inline:  0x404180   <- SAME! (per-binary singleton)
```

## 3. Level 2: Dynamic Shared Object Scope

### Problem

Why `inline` fails across shared library (.so) boundaries

### Mechanism

`-fvisibility=hidden` prevents symbol merging across DSO boundaries, demonstrating that each .so has its own instance.

### Key Code

**Header with inline variable (same for all DSOs)**

```cpp
// logger.hpp
inline Logger g_logger;

inline Logger& get_logger() { return g_logger; }
```

**CMake: Hide symbols to demonstrate per-DSO behavior**

```cpp
# CMakeLists.txt
target_compile_options(dso_plugin_a PRIVATE -fvisibility=hidden)
target_compile_options(dso_plugin_b PRIVATE -fvisibility=hidden)
```

**Plugin entry with explicit visibility**

```cpp
// libplugin_a.cpp
extern "C" __attribute__((visibility("default")))
void plugin_a_entry() {
    std::cout << "[plugin_a] logger @" << &get_logger() << "\n";
}
```

### Expected Output

```
Logger ctor @0x7f1234...   (main's instance)
Logger ctor @0x7f5678...   (plugin_a's instance)
Logger ctor @0x7f9abc...   (plugin_b's instance)
[main]     0x7f1234...
[plugin_a] 0x7f5678...     <- DIFFERENT!
[plugin_b] 0x7f9abc...     <- DIFFERENT!
```

## 4. Level 3: Thread-Local Scope

### Problem

Need per-thread singleton (orthogonal to binary/process scope)

### Mechanism

`thread_local` combined with `inline` creates a per-thread, cross-DSO singleton.

### Key Code

**Per-thread singleton with cross-DSO sharing**

```cpp
// thread_logger.hpp
struct ThreadLogger {
    ThreadLogger() {
        std::cout << "ThreadLogger ctor @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }
};

// C++17: inline thread_local - per-thread, shared across DSOs
inline thread_local ThreadLogger g_thread_logger;

inline ThreadLogger& get_thread_logger() {
    return g_thread_logger;
}
```

### Expected Output

```
ThreadLogger ctor @0xAAA tid=1  (main thread)
ThreadLogger ctor @0xBBB tid=2  (worker thread)
ThreadLogger ctor @0xCCC tid=3  (worker thread)
[main]     @0xAAA tid=1
[worker 0] @0xBBB tid=2   <- Different address, different thread
[worker 1] @0xCCC tid=3   <- Different address, different thread
```

## 5. Level 4: Process Scope

### Problem

Guarantee ONE instance across all DSOs in a process

### Why Needed

Multiple strategies exist to achieve a true process-wide singleton that all DSOs can share.

### Four Implementation Patterns

#### Core Shared Library (Recommended)

**Concept:** Central library owns the singleton; all other DSOs link to it.


**Singleton lives in dedicated core library**

```cpp
// core_api.cpp - THE singleton instance lives here
static ProcessLogger g_logger("core_shared_lib");

ProcessLogger& get_process_logger() {
    return g_logger;
}

// core_api.hpp
ProcessLogger& get_process_logger();
```

**All DSOs link to core library**

```cpp
# CMakeLists.txt
add_library(process_core SHARED core_api.cpp)
target_link_libraries(process_libA PRIVATE process_core)
target_link_libraries(process_libB PRIVATE process_core)
```

- **Pros:** Most straightforward, linker handles resolution, cross-platform
- **Cons:** Requires extra library

#### Main Executable Owner

**Concept:** Executable owns singleton; exports symbol for DSOs to find via `--export-dynamic`.


**Main exports singleton getter**

```cpp
// main.cpp - THE singleton instance lives here
static ProcessLogger g_logger("main_owner");

extern "C" ProcessLogger& get_process_logger() {
    return g_logger;
}
```

**Linker flag to export main's symbols**

```cpp
# CMakeLists.txt
target_link_options(main_owner_demo PRIVATE "-Wl,--export-dynamic")
```

- **Pros:** No extra library, main is clearly central
- **Cons:** Platform-specific linker flags, security exposure

#### dlsym Runtime Lookup

**Concept:** DSOs find singleton at runtime via `dlsym(RTLD_DEFAULT, ...)`.


**Runtime symbol resolution**

```cpp
// dso_common.cpp
#include <dlfcn.h>

using GetLoggerFn = ProcessLogger& (*)();

ProcessLogger& get_logger_via_dlsym() {
    static GetLoggerFn fn = nullptr;
    if (!fn) {
        // RTLD_DEFAULT: search all loaded shared objects
        void* sym = dlsym(RTLD_DEFAULT, "get_process_logger");
        if (!sym) {
            throw std::runtime_error("get_process_logger not found");
        }
        fn = reinterpret_cast<GetLoggerFn>(sym);
    }
    return (*fn)();
}
```

- **Pros:** True late binding, flexible plugin loading
- **Cons:** Complex debugging, runtime overhead, error handling required

#### Shared Memory

**Concept:** Kernel-backed shared memory with placement new for cross-process potential.


**shm_open + mmap + placement new**

```cpp
// shm_logger.cpp
#include <sys/mman.h>
#include <fcntl.h>

static const char* SHM_NAME = "/process_scope_logger";

ProcessLogger& get_shm_logger() {
    static ShmBlock* g_block = nullptr;
    static std::once_flag g_init_flag;

    std::call_once(g_init_flag, []() {
        int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
        ftruncate(fd, sizeof(ShmBlock));

        void* addr = mmap(nullptr, sizeof(ShmBlock),
                          PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);

        g_block = static_cast<ShmBlock*>(addr);

        // One-time initialization using atomic flag
        bool expected = false;
        if (g_block->initialized.compare_exchange_strong(expected, true)) {
            new (g_block->storage) ProcessLogger("shared_memory");
        }
    });

    return *reinterpret_cast<ProcessLogger*>(g_block->storage);
}
```

- **Pros:** Can extend to cross-process, no symbol visibility issues
- **Cons:** Complex, cleanup required, POSIX-specific

### Expected Output (All Variants)

```
[main] logger @0x7f1234...
[libA] logger @0x7f1234...  <- SAME!
[libB] logger @0x7f1234...  <- SAME!
[libC] logger @0x7f1234...  <- SAME!
```

## 6. Level 5: OS (Machine-Wide) Scope

### Problem

Ensure only ONE process instance runs on the entire machine

### Mechanism

`flock()` with exclusive non-blocking lock on a lock file in `/tmp`.

### Key Code

**flock with LOCK_EX | LOCK_NB for exclusive non-blocking lock**

```cpp
// singleton_daemon.cpp
#include <sys/file.h>
#include <fcntl.h>
#include <unistd.h>

constexpr const char* LOCK_FILE = "/tmp/os_scope_singleton.lock";

int main() {
    int fd = open(LOCK_FILE, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        std::cerr << "Failed to open lock file\n";
        return 1;
    }

    // Try to acquire exclusive lock (non-blocking)
    if (flock(fd, LOCK_EX | LOCK_NB) < 0) {
        if (errno == EWOULDBLOCK) {
            std::cerr << "Another instance is already running!\n";
        }
        close(fd);
        return 1;
    }

    // Lock acquired - we are the singleton
    std::cout << "Lock acquired! This is the singleton instance.\n";

    // ... do work ...

    close(fd);  // Lock auto-released
    return 0;
}
```

### Expected Output

```
Terminal 1:
$ ./os_scope_demo
Lock acquired! This is the singleton instance.
Press Enter to release lock and exit...

Terminal 2 (simultaneously):
$ ./os_scope_demo
Another instance is already running!
```

## 7. Comparison Table

| Scope | Mechanism | Key C++ Feature | Guarantee |
|-------|-----------|-----------------|-----------|
| tu_scope | ODR + linkage | `static` vs `inline` | Per-TU / Per-binary |
| dso_scope | Symbol visibility | `-fvisibility=hidden` | Per-DSO |
| thread_scope | TLS | `thread_local` | Per-thread |
| process_scope | Various (4 variants) | Linker/dlsym/shm | Per-process |
| os_scope | Kernel lock | `flock()` | Per-machine |

## 8. Key Takeaways

### 8.1 Common Pitfalls

| Pitfall | Consequence |
|---------|-------------|
| `static` in header | Creates per-TU copies (not singleton!) |
| Trusting `inline` across DSOs | Each .so gets its own copy |
| Forgetting `-fvisibility=hidden` | Unexpected symbol merging |
| Confusing `thread_local` with process-wide | Per-thread, not process singleton |
| Over-engineering scope level | Using os_scope when process_scope suffices |

### 8.2 When to Use Which

| Scenario | Recommended Scope |
|----------|-------------------|
| Header-only library, single binary | `tu_scope` with `inline` |
| Plugin architecture, intentional isolation | `dso_scope` |
| Request context, per-thread state | `thread_scope` |
| Multi-DSO application, shared logger/config | `process_scope` (core_shared_lib) |
| Daemon process, prevent duplicate instances | `os_scope` |

### Quick Decision Flow

```
Do you need one instance per THREAD?
  └─ Yes → thread_scope (thread_local)
  └─ No ↓

Do you need one instance per MACHINE?
  └─ Yes → os_scope (flock)
  └─ No ↓

Do you have multiple DSOs/shared libraries?
  └─ Yes → process_scope (core_shared_lib recommended)
  └─ No ↓

Single binary with multiple TUs?
  └─ Yes → tu_scope (inline)
```
