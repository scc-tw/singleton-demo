#!/usr/bin/env python3
"""
Singleton Scope Report Generator

Generates a Markdown report for the C++ singleton scope tutorial,
suitable for presentation slides.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = PROJECT_ROOT / "singleton_scope_report.md"


# =============================================================================
# SCOPE DEFINITIONS
# =============================================================================

SCOPE_DEFINITIONS: Dict[str, Any] = {
    "tu_scope": {
        "level": 1,
        "title": "Translation Unit Scope",
        "problem": "Why `static` in header fails to create a true singleton",
        "concept": "Each translation unit (`.cpp` file) that includes the header gets its own copy of a `static` variable. This violates the singleton pattern.",
        "mechanism": "C++17 `inline` variable guarantees a single instance across the entire binary, regardless of how many TUs include the header.",
        "key_code": [
            {
                "description": "The Pitfall: `static` creates per-TU copies",
                "snippet": """// logger_static.hpp - WARNING: Each TU gets its own copy!
static Logger g_logger_static;

static Logger& get_logger_static() {
    return g_logger_static;
}"""
            },
            {
                "description": "The Solution: `inline` ensures one instance (C++17)",
                "snippet": """// logger_inline.hpp - Single instance across entire binary
inline Logger g_logger_inline;

inline Logger& get_logger_inline() {
    return g_logger_inline;
}"""
            }
        ],
        "expected_output_source": "tu_scope/plan.md",
        "expected_output_fallback": """[user_a] static:  0x404100
[user_a] inline:  0x404180
[user_b] static:  0x404120   <- DIFFERENT! (per-TU copy)
[user_b] inline:  0x404180   <- SAME! (per-binary singleton)"""
    },

    "dso_scope": {
        "level": 2,
        "title": "Dynamic Shared Object Scope",
        "problem": "Why `inline` fails across shared library (.so) boundaries",
        "concept": "Each DSO (shared library) maintains its own data section. Even with `inline`, the linker treats each DSO as a separate unit, creating multiple copies.",
        "mechanism": "`-fvisibility=hidden` prevents symbol merging across DSO boundaries, demonstrating that each .so has its own instance.",
        "key_code": [
            {
                "description": "Header with inline variable (same for all DSOs)",
                "snippet": """// logger.hpp
inline Logger g_logger;

inline Logger& get_logger() { return g_logger; }"""
            },
            {
                "description": "CMake: Hide symbols to demonstrate per-DSO behavior",
                "snippet": """# CMakeLists.txt
target_compile_options(dso_plugin_a PRIVATE -fvisibility=hidden)
target_compile_options(dso_plugin_b PRIVATE -fvisibility=hidden)"""
            },
            {
                "description": "Plugin entry with explicit visibility",
                "snippet": """// libplugin_a.cpp
extern "C" __attribute__((visibility("default")))
void plugin_a_entry() {
    std::cout << "[plugin_a] logger @" << &get_logger() << "\\n";
}"""
            }
        ],
        "expected_output_source": "dso_scope/plan.md",
        "expected_output_fallback": """Logger ctor @0x7f1234...   (main's instance)
Logger ctor @0x7f5678...   (plugin_a's instance)
Logger ctor @0x7f9abc...   (plugin_b's instance)
[main]     0x7f1234...
[plugin_a] 0x7f5678...     <- DIFFERENT!
[plugin_b] 0x7f9abc...     <- DIFFERENT!"""
    },

    "thread_scope": {
        "level": 3,
        "title": "Thread-Local Scope",
        "problem": "Need per-thread singleton (orthogonal to binary/process scope)",
        "concept": "Each thread gets its own instance. Within the same thread, the instance is shared across DSOs (if symbols are visible).",
        "mechanism": "`thread_local` combined with `inline` creates a per-thread, cross-DSO singleton.",
        "key_code": [
            {
                "description": "Per-thread singleton with cross-DSO sharing",
                "snippet": """// thread_logger.hpp
struct ThreadLogger {
    ThreadLogger() {
        std::cout << "ThreadLogger ctor @" << this
                  << " tid=" << std::this_thread::get_id() << "\\n";
    }
};

// C++17: inline thread_local - per-thread, shared across DSOs
inline thread_local ThreadLogger g_thread_logger;

inline ThreadLogger& get_thread_logger() {
    return g_thread_logger;
}"""
            }
        ],
        "expected_output_source": "thread_scope/plan.md",
        "expected_output_fallback": """ThreadLogger ctor @0xAAA tid=1  (main thread)
ThreadLogger ctor @0xBBB tid=2  (worker thread)
ThreadLogger ctor @0xCCC tid=3  (worker thread)
[main]     @0xAAA tid=1
[worker 0] @0xBBB tid=2   <- Different address, different thread
[worker 1] @0xCCC tid=3   <- Different address, different thread"""
    },

    "process_scope": {
        "level": 4,
        "title": "Process Scope",
        "problem": "Guarantee ONE instance across all DSOs in a process",
        "concept": "Multiple strategies exist to achieve a true process-wide singleton that all DSOs can share.",
        "mechanism": "Four approaches: core library, symbol export, runtime lookup, or shared memory.",
        "variants": {
            "core_shared_lib": {
                "title": "Core Shared Library (Recommended)",
                "concept": "Central library owns the singleton; all other DSOs link to it.",
                "key_code": [
                    {
                        "description": "Singleton lives in dedicated core library",
                        "snippet": """// core_api.cpp - THE singleton instance lives here
static ProcessLogger g_logger("core_shared_lib");

ProcessLogger& get_process_logger() {
    return g_logger;
}

// core_api.hpp
ProcessLogger& get_process_logger();"""
                    },
                    {
                        "description": "All DSOs link to core library",
                        "snippet": """# CMakeLists.txt
add_library(process_core SHARED core_api.cpp)
target_link_libraries(process_libA PRIVATE process_core)
target_link_libraries(process_libB PRIVATE process_core)"""
                    }
                ],
                "pros": "Most straightforward, linker handles resolution, cross-platform",
                "cons": "Requires extra library"
            },
            "main_owner": {
                "title": "Main Executable Owner",
                "concept": "Executable owns singleton; exports symbol for DSOs to find via `--export-dynamic`.",
                "key_code": [
                    {
                        "description": "Main exports singleton getter",
                        "snippet": """// main.cpp - THE singleton instance lives here
static ProcessLogger g_logger("main_owner");

extern "C" ProcessLogger& get_process_logger() {
    return g_logger;
}"""
                    },
                    {
                        "description": "Linker flag to export main's symbols",
                        "snippet": """# CMakeLists.txt
target_link_options(main_owner_demo PRIVATE "-Wl,--export-dynamic")"""
                    }
                ],
                "pros": "No extra library, main is clearly central",
                "cons": "Platform-specific linker flags, security exposure"
            },
            "dlsym_default": {
                "title": "dlsym Runtime Lookup",
                "concept": "DSOs find singleton at runtime via `dlsym(RTLD_DEFAULT, ...)`.",
                "key_code": [
                    {
                        "description": "Runtime symbol resolution",
                        "snippet": """// dso_common.cpp
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
}"""
                    }
                ],
                "pros": "True late binding, flexible plugin loading",
                "cons": "Complex debugging, runtime overhead, error handling required"
            },
            "shared_memory": {
                "title": "Shared Memory",
                "concept": "Kernel-backed shared memory with placement new for cross-process potential.",
                "key_code": [
                    {
                        "description": "shm_open + mmap + placement new",
                        "snippet": """// shm_logger.cpp
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
}"""
                    }
                ],
                "pros": "Can extend to cross-process, no symbol visibility issues",
                "cons": "Complex, cleanup required, POSIX-specific"
            }
        },
        "expected_output_fallback": """[main] logger @0x7f1234...
[libA] logger @0x7f1234...  <- SAME!
[libB] logger @0x7f1234...  <- SAME!
[libC] logger @0x7f1234...  <- SAME!"""
    },

    "os_scope": {
        "level": 5,
        "title": "OS (Machine-Wide) Scope",
        "problem": "Ensure only ONE process instance runs on the entire machine",
        "concept": "Use kernel-level locking to prevent duplicate process instances. Common for daemon processes.",
        "mechanism": "`flock()` with exclusive non-blocking lock on a lock file in `/tmp`.",
        "key_code": [
            {
                "description": "flock with LOCK_EX | LOCK_NB for exclusive non-blocking lock",
                "snippet": """// singleton_daemon.cpp
#include <sys/file.h>
#include <fcntl.h>
#include <unistd.h>

constexpr const char* LOCK_FILE = "/tmp/os_scope_singleton.lock";

int main() {
    int fd = open(LOCK_FILE, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        std::cerr << "Failed to open lock file\\n";
        return 1;
    }

    // Try to acquire exclusive lock (non-blocking)
    if (flock(fd, LOCK_EX | LOCK_NB) < 0) {
        if (errno == EWOULDBLOCK) {
            std::cerr << "Another instance is already running!\\n";
        }
        close(fd);
        return 1;
    }

    // Lock acquired - we are the singleton
    std::cout << "Lock acquired! This is the singleton instance.\\n";

    // ... do work ...

    close(fd);  // Lock auto-released
    return 0;
}"""
            }
        ],
        "expected_output_source": "os_scope/plan.md",
        "expected_output_fallback": """Terminal 1:
$ ./os_scope_demo
Lock acquired! This is the singleton instance.
Press Enter to release lock and exit...

Terminal 2 (simultaneously):
$ ./os_scope_demo
Another instance is already running!"""
    }
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_code_block(code: str, lang: str = "cpp") -> str:
    """Wrap code in markdown fenced code block."""
    return f"```{lang}\n{code.strip()}\n```"


def format_output_block(output: str) -> str:
    """Wrap output in markdown fenced code block."""
    return f"```\n{output.strip()}\n```"


def extract_expected_output(plan_path: Path) -> Optional[str]:
    """
    Extract expected output from plan.md files.
    Looks for sections starting with '## Expected' or '## 預期'.
    """
    if not plan_path.exists():
        return None

    content = plan_path.read_text(encoding="utf-8")

    # Match expected result section (handles both English and Chinese headers)
    # Look for code block after the header
    pattern = r'##\s*(?:Expected|預期)[^\n]*\n+```(?:\w+)?\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return None


# =============================================================================
# SECTION GENERATORS
# =============================================================================

def generate_overview() -> str:
    """Generate the overview section."""
    return """# C++ Singleton Scope Tutorial Report

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
5. **os_scope** — Machine-wide: Kernel locks"""


def generate_scope_section(scope_key: str, scope_data: dict) -> str:
    """Generate markdown section for a scope level."""
    level = scope_data["level"]
    title = scope_data["title"]

    sections = [
        f"## {level + 1}. Level {level}: {title}",
        "",
        f"### Problem",
        "",
        scope_data["problem"],
        "",
        f"### Mechanism",
        "",
        scope_data["mechanism"],
        "",
        f"### Key Code",
    ]

    # Add code snippets
    for code_item in scope_data.get("key_code", []):
        sections.append(f"\n**{code_item['description']}**\n")
        sections.append(format_code_block(code_item["snippet"]))

    # Add expected output
    sections.append("\n### Expected Output\n")

    # Try to extract from plan.md, fall back to hardcoded
    output = None
    if "expected_output_source" in scope_data:
        plan_path = PROJECT_ROOT / scope_data["expected_output_source"]
        output = extract_expected_output(plan_path)

    if not output:
        output = scope_data.get("expected_output_fallback", "")

    sections.append(format_output_block(output))

    return "\n".join(sections)


def generate_process_scope_section() -> str:
    """Generate the process_scope section with all 4 variants."""
    scope_data = SCOPE_DEFINITIONS["process_scope"]
    level = scope_data["level"]
    title = scope_data["title"]

    sections = [
        f"## {level + 1}. Level {level}: {title}",
        "",
        f"### Problem",
        "",
        scope_data["problem"],
        "",
        f"### Why Needed",
        "",
        scope_data["concept"],
        "",
        "### Four Implementation Patterns",
    ]

    # Add each variant
    for var_key, var_data in scope_data["variants"].items():
        sections.append(f"\n#### {var_data['title']}\n")
        sections.append(f"**Concept:** {var_data['concept']}\n")

        # Add code snippets
        for code_item in var_data.get("key_code", []):
            sections.append(f"\n**{code_item['description']}**\n")
            sections.append(format_code_block(code_item["snippet"]))

        # Pros/Cons
        sections.append(f"\n- **Pros:** {var_data.get('pros', 'N/A')}")
        sections.append(f"- **Cons:** {var_data.get('cons', 'N/A')}")

    # Add expected output (same for all variants when working correctly)
    sections.append("\n### Expected Output (All Variants)\n")
    output = scope_data.get("expected_output_fallback", "")
    sections.append(format_output_block(output))

    return "\n".join(sections)


def generate_comparison_table() -> str:
    """Generate the comparison table."""
    return """## 7. Comparison Table

| Scope | Mechanism | Key C++ Feature | Guarantee |
|-------|-----------|-----------------|-----------|
| tu_scope | ODR + linkage | `static` vs `inline` | Per-TU / Per-binary |
| dso_scope | Symbol visibility | `-fvisibility=hidden` | Per-DSO |
| thread_scope | TLS | `thread_local` | Per-thread |
| process_scope | Various (4 variants) | Linker/dlsym/shm | Per-process |
| os_scope | Kernel lock | `flock()` | Per-machine |"""


def generate_takeaways() -> str:
    """Generate common pitfalls and when-to-use recommendations."""
    return """## 8. Key Takeaways

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
```"""


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Generate the singleton scope report."""
    print(f"Generating report...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output file: {OUTPUT_FILE}")

    # Generate all sections
    sections = [
        generate_overview(),
        generate_scope_section("tu_scope", SCOPE_DEFINITIONS["tu_scope"]),
        generate_scope_section("dso_scope", SCOPE_DEFINITIONS["dso_scope"]),
        generate_scope_section("thread_scope", SCOPE_DEFINITIONS["thread_scope"]),
        generate_process_scope_section(),
        generate_scope_section("os_scope", SCOPE_DEFINITIONS["os_scope"]),
        generate_comparison_table(),
        generate_takeaways(),
    ]

    report = "\n\n".join(sections)

    # Write output
    OUTPUT_FILE.write_text(report, encoding="utf-8")

    print(f"\nReport generated successfully!")
    print(f"Size: {len(report):,} characters")
    print(f"Lines: {report.count(chr(10)):,}")


if __name__ == "__main__":
    main()
