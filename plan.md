# Singleton Scope Lab — Master Plan

## 專案總覽

這是一個 C++ singleton 作用域教學專案，從最小的 Translation Unit 到整台機器，逐層展示 singleton 的不同作用範圍與實作方式。

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Singleton Scope Hierarchy                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐                                                   │
│   │  os_scope   │  ← 整台機器只有一份 (kernel object / flock)        │
│   └──────┬──────┘                                                   │
│          │                                                          │
│   ┌──────▼──────┐                                                   │
│   │process_scope│  ← 整個 process 只有一份 (跨 DSO)                  │
│   │  4 variants │     • core_shared_lib (正派)                      │
│   │             │     • main_owner (main export)                    │
│   │             │     • dlsym_default (runtime lookup)              │
│   │             │     • shared_memory (kernel object)               │
│   └──────┬──────┘                                                   │
│          │                                                          │
│   ┌──────▼──────┐                                                   │
│   │ thread_scope│  ← 每個 thread 各一份 (thread_local)              │
│   └──────┬──────┘                                                   │
│          │                                                          │
│   ┌──────▼──────┐                                                   │
│   │  dso_scope  │  ← 每個 shared library 各一份                     │
│   └──────┬──────┘                                                   │
│          │                                                          │
│   ┌──────▼──────┐                                                   │
│   │  tu_scope   │  ← 每個 Translation Unit 各一份 (static)          │
│   └─────────────┘    vs 整個 binary 一份 (inline)                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 專案結構

```txt
singleton-scope-lab/
├── CMakeLists.txt          # 頂層 CMake
├── plan.md                 # 本文件（總覽）
│
├── tu_scope/               # 1. Translation Unit level
│   ├── plan.md
│   ├── CMakeLists.txt
│   ├── logger.hpp
│   ├── logger_static.cpp
│   ├── logger_inline.hpp
│   ├── user_a.cpp
│   ├── user_b.cpp
│   └── main.cpp
│
├── dso_scope/              # 2. Dynamic Shared Object level
│   ├── plan.md
│   ├── CMakeLists.txt
│   ├── logger.hpp
│   ├── libplugin_a.cpp
│   ├── libplugin_b.cpp
│   └── main.cpp
│
├── thread_scope/           # 3. Thread-local level
│   ├── plan.md
│   ├── CMakeLists.txt
│   ├── thread_logger.hpp
│   ├── basic_demo.cpp
│   ├── mixed_demo.cpp
│   └── libworker.cpp
│
├── process_scope/          # 4. Process level (重頭戲)
│   ├── plan.md
│   ├── CMakeLists.txt
│   ├── include/
│   │   └── process_logger.hpp
│   │
│   ├── core_shared_lib/    # Variant 1: 正派作法
│   │   ├── CMakeLists.txt
│   │   ├── core_api.cpp
│   │   ├── main.cpp
│   │   ├── libA.cpp
│   │   ├── libB.cpp
│   │   └── libC.cpp
│   │
│   ├── main_owner/         # Variant 2: main 當 owner
│   │   ├── CMakeLists.txt
│   │   ├── main.cpp
│   │   ├── libA.cpp
│   │   ├── libB.cpp
│   │   └── libC.cpp
│   │
│   ├── dlsym_default/      # Variant 3: dlsym runtime lookup
│   │   ├── CMakeLists.txt
│   │   ├── main.cpp
│   │   ├── dso_common.cpp
│   │   ├── libA.cpp
│   │   ├── libB.cpp
│   │   └── libC.cpp
│   │
│   └── shared_memory/      # Variant 4: shared memory
│       ├── CMakeLists.txt
│       ├── shm_logger.hpp
│       ├── shm_logger.cpp
│       ├── main.cpp
│       ├── libA.cpp
│       ├── libB.cpp
│       └── libC.cpp
│
└── os_scope/               # 5. Machine level
    ├── plan.md
    ├── CMakeLists.txt
    └── singleton_daemon.cpp
```

## 頂層 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.12)
project(singleton_scope_lab CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 方便 demo 時看到 .so 檔案
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

add_subdirectory(tu_scope)
add_subdirectory(dso_scope)
add_subdirectory(thread_scope)
add_subdirectory(process_scope)
add_subdirectory(os_scope)
```

## 編譯與執行

```bash
# 建立 build 目錄
mkdir build && cd build

# 編譯全部
cmake .. && make -j$(nproc)

# 執行各 demo
./bin/tu_scope_demo
./bin/dso_scope_demo
./bin/thread_scope_demo
./bin/process_core_demo
./bin/main_owner_demo
./bin/dlsym_demo
./bin/shm_demo
./bin/os_scope_demo
```

## 學習路徑

### 建議順序

```
1. tu_scope      →  理解 TU 與 inline variable
       ↓
2. dso_scope     →  理解為什麼 inline 跨 DSO 會破功
       ↓
3. thread_scope  →  thread_local 的用途（支線）
       ↓
4. process_scope →  四種解法比較（核心）
   ├── core_shared_lib  →  最正規
   ├── main_owner       →  main export symbols
   ├── dlsym_default    →  runtime lookup（黑魔法）
   └── shared_memory    →  為 os_scope 鋪路
       ↓
5. os_scope      →  跨 process 的 singleton
```

### 關鍵知識點對照

| Scope | 關鍵機制 | C++ 語法 | 平台相依 |
|-------|---------|---------|---------|
| tu_scope | ODR, linkage | `static`, `inline` | 無 |
| dso_scope | dynamic linker | `inline`, visibility | 部分 |
| thread_scope | TLS | `thread_local` | 無 |
| process_scope | symbol resolution | `extern "C"`, dlsym | 是 |
| os_scope | kernel object | flock, shm | 是 (POSIX) |

## 各 Scope 快速對比

### 1. tu_scope — 陷阱示範

```cpp
// header 中的 static → 每個 TU 一份（通常是 bug）
static Logger g_logger;

// C++17 inline → 整個 binary 一份（正確）
inline Logger g_logger;
```

**結果**：static 版本 user_a 和 user_b 拿到不同位址

---

### 2. dso_scope — inline 的極限

```cpp
// 即使用 inline，跨 DSO 仍然各一份
inline Logger g_logger;  // main.cpp 裡一份
inline Logger g_logger;  // libplugin_a.so 裡一份
inline Logger g_logger;  // libplugin_b.so 裡一份
```

**結果**：main, plugin_a, plugin_b 三個不同位址

---

### 3. thread_scope — 刻意的 per-thread

```cpp
inline thread_local Logger g_logger;  // 每個 thread 各一份
```

**結果**：N 個 thread 印出 N 個不同位址

---

### 4. process_scope — 四種解法

| Variant | 核心概念 | 複雜度 | 跨平台 |
|---------|---------|-------|-------|
| core_shared_lib | 所有人 link 同一個 .so | ★★☆ | 好 |
| main_owner | main export, DSO extern | ★★☆ | 中 |
| dlsym_default | runtime symbol lookup | ★★★ | 中 |
| shared_memory | kernel object backing | ★★★★ | POSIX |

**結果**：四種方法都讓 main + libA/B/C 拿到同一個位址

---

### 5. os_scope — 跨 process

```cpp
// 用 flock 確保整台機器只有一個 instance
flock(fd, LOCK_EX | LOCK_NB);
```

**結果**：第二個 process 啟動失敗

---

## 延伸討論

### 為什麼這很重要？

1. **Plugin 架構**：host + plugin 如何共享 logger / config
2. **Memory 效率**：避免重複初始化大型資源
3. **狀態一致性**：確保全局狀態的唯一性
4. **Thread safety**：理解 static initialization 的 thread safety

### 常見踩坑

| 問題 | 原因 | 解法 |
|------|-----|-----|
| Logger 位址不一致 | per-TU static | 用 inline 或 .cpp 定義 |
| Plugin 各自 logger | per-DSO inline | 用 core library |
| Race condition | static init order | Meyer's singleton |
| 跨 process 不共享 | process isolation | shared memory |

### 進階主題（未涵蓋）

- **SIOF** (Static Initialization Order Fiasco)
- **Meyer's Singleton** 與 C++11 thread safety
- **Dependency Injection** 取代 singleton
- **Service Locator** pattern

## 實作進度追蹤

- [ ] 頂層 CMakeLists.txt
- [ ] tu_scope/ 完整實作
- [ ] dso_scope/ 完整實作
- [ ] thread_scope/ 完整實作
- [ ] process_scope/
  - [ ] include/process_logger.hpp
  - [ ] core_shared_lib/
  - [ ] main_owner/
  - [ ] dlsym_default/
  - [ ] shared_memory/
- [ ] os_scope/ 完整實作

---

**下一步**：選一個資料夾開始實作，建議從 `tu_scope/` 或 `process_scope/core_shared_lib/` 開始。
