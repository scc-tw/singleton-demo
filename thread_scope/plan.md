# thread_scope/ — Thread-Local Singleton Demo

## 目標

展示 `thread_local` 讓每個 thread 各有一份 singleton 實體。

## 檔案結構

```txt
thread_scope/
  CMakeLists.txt
  thread_logger.hpp    # thread_local logger
  main.cpp             # spawn N 個 worker 印位址
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

    void log(const char* msg) {
        std::cout << "[" << msg << "] @" << this
                  << " tid=" << std::this_thread::get_id() << "\n";
    }
};

inline thread_local ThreadLogger g_thread_logger;

inline ThreadLogger& get_thread_logger() {
    return g_thread_logger;
}
```

### main.cpp
```cpp
#include "thread_logger.hpp"
#include <thread>
#include <vector>

void worker(int id) {
    get_thread_logger().log(("worker " + std::to_string(id)).c_str());
}

int main() {
    get_thread_logger().log("main");

    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(worker, i);
    }

    for (auto& t : threads) {
        t.join();
    }
}
```

## CMakeLists.txt 概要

```cmake
add_executable(thread_scope_demo main.cpp)
target_link_libraries(thread_scope_demo PRIVATE pthread)
```

## 預期結果

執行 `thread_scope_demo` 後：
```
ThreadLogger ctor @0x7f1111 tid=main_tid
[main] @0x7f1111 tid=main_tid
ThreadLogger ctor @0x7f2222 tid=worker0_tid
ThreadLogger ctor @0x7f3333 tid=worker1_tid
ThreadLogger ctor @0x7f4444 tid=worker2_tid
[worker 0] @0x7f2222 tid=worker0_tid
[worker 1] @0x7f3333 tid=worker1_tid
[worker 2] @0x7f4444 tid=worker2_tid
```

每個 thread 印出**不同**位址 → **per-thread scope**

## 教學重點

1. `thread_local` storage duration 的語意
2. `inline thread_local` 的組合使用
3. Thread-local singleton 的應用場景
   - Per-thread cache
   - Thread-specific context
   - 避免 lock contention
4. 與 process scope 的差異
