# process_scope/ — Process-Level Singleton Demo

## 目標

展示多個 DSO（main + libA.so + libB.so + libC.so）但整個 process 只有一份 singleton 的**四種實作方法**。

這是本專案的重頭戲，比較不同方法的優缺點與適用場景。

## 資料夾結構

```txt
process_scope/
  CMakeLists.txt
  include/
    process_logger.hpp        # 共用 Logger 定義

  core_shared_lib/            # Variant 1: 正派作法 - core shared library
  main_owner/                 # Variant 2: main 當 owner，DSO 只 extern
  dlsym_default/              # Variant 3: dlsym(RTLD_DEFAULT) runtime lookup
  shared_memory/              # Variant 4: shared memory (kernel object)
```

## 共用 Header: include/process_logger.hpp

```cpp
#pragma once
#include <iostream>

struct ProcessLogger {
    ProcessLogger(const char* tag);
    void log(const char* who) const;
};
```

---

## Variant 1: core_shared_lib/ — 正派作法

### 概念
建立 `libprocess_core.so`，持有唯一 `ProcessLogger` 實體並提供 getter。
所有 image（main, libA/B/C）都 **link** 這個 core library。

### 結構
```txt
core_shared_lib/
  CMakeLists.txt
  core_api.cpp      # 定義 ProcessLogger 實作 + get_process_logger()
  main.cpp
  libA.cpp
  libB.cpp
  libC.cpp
```

### 關鍵程式碼
- `core_api.cpp`: 定義 `static ProcessLogger g_logger` + `get_process_logger()`
- `libA/B/C.cpp`: 呼叫 `get_process_logger().log("libX")`
- `main.cpp`: 呼叫所有 entry points

### 優點
- 最正規、最易理解
- Symbol resolution 由 linker 處理
- 跨平台相容性好

### 缺點
- 需要額外的 core library

---

## Variant 2: main_owner/ — Main 當 Owner

### 概念
- 唯一實體 & getter **定義在 main executable**
- `libA/B/C` 只宣告 `extern "C" ProcessLogger& get_process_logger();`
- 透過 `-rdynamic` / `--export-dynamic` 讓 DSO 找到 main 的定義

### 結構
```txt
main_owner/
  CMakeLists.txt
  main.cpp          # 定義唯一 logger + getter
  libA.cpp
  libB.cpp
  libC.cpp
```

### 關鍵 CMake
```cmake
target_link_options(main_owner_demo PRIVATE "-Wl,--export-dynamic")
```

### 優點
- 不需要額外 library
- 適合 main 確實是「核心」的架構

### 缺點
- 依賴平台特定的 linker flag
- Main 必須 export symbols（安全性考量）

---

## Variant 3: dlsym_default/ — Runtime Symbol Lookup

### 概念
- main 定義 `get_process_logger()`
- DSO 在 **runtime** 用 `dlsym(RTLD_DEFAULT, "get_process_logger")` 找函式指標
- 不需要 link-time symbol resolution

### 結構
```txt
dlsym_default/
  CMakeLists.txt
  main.cpp          # 定義 logger + getter
  dso_common.cpp    # 給三個 DSO 共用的 dlsym helper
  libA.cpp
  libB.cpp
  libC.cpp
```

### 關鍵程式碼
```cpp
// dso_common.cpp
GetLoggerFn resolve_get_logger() {
    void* sym = dlsym(RTLD_DEFAULT, "get_process_logger");
    if (!sym) throw std::runtime_error("get_process_logger not found");
    return reinterpret_cast<GetLoggerFn>(sym);
}
```

### 優點
- 真正的 late binding
- 可以處理更複雜的 plugin 載入順序

### 缺點
- 黑魔法，較難 debug
- 需要 error handling
- Runtime overhead（首次查找）

---

## Variant 4: shared_memory/ — Kernel Object

### 概念
- 使用 POSIX shared memory (`shm_open`) 作為 backing storage
- 多個 DSO 透過同一個名字 `"/process_scope_logger"` 取得同一塊記憶體
- 在 shared memory 上用 placement new 建構 `ProcessLogger`

### 結構
```txt
shared_memory/
  CMakeLists.txt
  shm_logger.hpp    # shm/mmap helper 宣告
  shm_logger.cpp    # shm/mmap + placement new 實作
  main.cpp
  libA.cpp
  libB.cpp
  libC.cpp
```

### 關鍵程式碼
```cpp
ProcessLogger& get_shm_logger() {
    static ShmBlock* block = nullptr;
    static std::once_flag flag;

    std::call_once(flag, [] {
        int fd = shm_open("/process_scope_logger", O_CREAT | O_RDWR, 0666);
        ftruncate(fd, sizeof(ShmBlock));
        void* addr = mmap(nullptr, sizeof(ShmBlock),
                          PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);
        block = static_cast<ShmBlock*>(addr);
        if (!block->initialized) {
            new (block->storage) ProcessLogger("shared_memory");
            block->initialized = true;
        }
    });

    return *reinterpret_cast<ProcessLogger*>(block->storage);
}
```

### 優點
- 可以跨 process（為 os_scope 鋪路）
- 不依賴 symbol visibility

### 缺點
- 複雜度高
- 需要處理 shm cleanup
- 需要 process-robust mutex（如果有 race condition）
- 平台相依（POSIX）

---

## 頂層 CMakeLists.txt

```cmake
add_library(process_logger_interface INTERFACE)
target_include_directories(process_logger_interface
    INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_subdirectory(core_shared_lib)
add_subdirectory(main_owner)
add_subdirectory(dlsym_default)
add_subdirectory(shared_memory)
```

## 教學重點

1. 為什麼需要 process-level singleton？（避免 dso_scope 的問題）
2. 四種方法的 trade-off 比較
3. Symbol visibility 與 dynamic linker 行為
4. 什麼時候該用哪種方法
5. shared_memory 版本為 os_scope 埋下伏筆
