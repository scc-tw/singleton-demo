# thread_scope/ — Thread-Local Singleton Demo

## 目標

展示 `thread_local` 讓每個 thread 各有一份 singleton 實體，並探討在跨 DSO (Dynamic Shared Object) 情境下的行為。

## 檔案結構

```txt
thread_scope/
  CMakeLists.txt
  thread_logger.hpp    # thread_local logger (inline thread_local)
  
  # 1. Basic Demo
  basic_demo.cpp       # spawn N 個 worker 印位址

  # 2. Cross-DSO Demo (混合情境)
  libworker.cpp        # Shared library, 提供 function 在 library 內存取 logger
  libworker.hpp
  mixed_demo.cpp       # Main exe + Shared lib 交互呼叫，驗證同一 thread 跨 DSO 是否一致
```

## 核心概念

### thread_logger.hpp
```cpp
#pragma once
#include <iostream>
#include <thread>

struct ThreadLogger {
    ThreadLogger() {
        std::cout << "ThreadLogger ctor @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }

    void log(const char* context) {
        std::cout << "[" << context << "] @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }
};

// 重點：inline thread_local
// C++17 保證跨 TU/DSO (若符號可見) 合併為同一個 per-thread instance
inline thread_local ThreadLogger g_thread_logger;

inline ThreadLogger& get_thread_logger() {
    return g_thread_logger;
}
```

## 實驗場景

### 1. Basic Demo (`basic_demo.cpp`)
單純在一個 executable 中產生多個 thread。
- **預期**：每個 thread 有獨立的 `ThreadLogger` instance。

### 2. Mixed Demo (`mixed_demo.cpp` + `libworker.so`)
探討 `thread_local` 跨越 DSO 邊界時的行為。
- **架構**：
    - `libworker.so`: 提供 `call_logger_in_lib()` 函式，內部呼叫 `get_thread_logger().log(...)`。
    - `mixed_demo`: 
        1. 在 main thread 呼叫 `get_thread_logger()` (Main scope)。
        2. 在 main thread 呼叫 `call_logger_in_lib()` (Lib scope)。
        3. 啟動 worker thread，重複上述步驟。
- **關鍵問題**：同一個 thread 在 "Main Executable" 和 "Shared Library" 中，看到的是同一個 `g_thread_logger` 嗎？
- **預期結果**：若是 `inline thread_local` 且 symbol 有正確 export (default visibility)，應該要**相同**。這展示了 `thread_local` 的 scope 是 "Per-Thread Global" 而非 "Per-Thread Per-Module"。

## CMakeLists.txt 規劃

```cmake
# Basic Demo
add_executable(thread_basic_demo basic_demo.cpp)
target_link_libraries(thread_basic_demo PRIVATE pthread)

# Mixed Demo
add_library(thread_worker SHARED libworker.cpp)
target_link_libraries(thread_worker PRIVATE pthread)

add_executable(thread_mixed_demo mixed_demo.cpp)
target_link_libraries(thread_mixed_demo PRIVATE thread_worker pthread)
```

## 教學重點

1. `thread_local` storage duration 的語意。
2. `inline thread_local` 的組合使用。
3. **跨 DSO 的 Thread-local**：
   - 驗證 C++ `inline` 變數在動態連結下的行為。
   - 比較 `static thread_local` (TU-local) vs `inline thread_local` (External linkage) 在此場景的差異。
4. 應用場景：
   - Request-scoped context (如 Web Server 處理 request)。
   - Error handling (類似 `errno`)。
