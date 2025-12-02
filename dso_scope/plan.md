# dso_scope/ — Dynamic Shared Object Level Singleton Demo

## 目標

展示「同一個 `inline` logger header，在不同 DSO（shared library）裡仍然各有一份」。

即使使用 C++17 `inline` variable，跨越 shared library 邊界時，每個 DSO 仍會有自己的實體。

## 檔案結構

```txt
dso_scope/
  CMakeLists.txt
  logger.hpp          # inline logger
  libplugin_a.cpp     # plugin A shared library
  libplugin_b.cpp     # plugin B shared library
  main.cpp            # 主程式
```

## 核心概念

### ODR 在 DSO 的邊界

標準 C++ 的 ODR 保證通常針對**單一執行檔 (Executable)**。
當跨越 DSO (Dynamic Shared Object) 邊界時，預設情況下（視作業系統與 Visibility 設定而定），每個 DSO 可能維護自己的 Global/Static 區域。
這並不算違反 ODR，因為每個 DSO 被視為獨立載入單元，但這會打破「全系統唯一」的 Singleton 預期。

### logger.hpp
```cpp
#pragma once
#include <iostream>

struct Logger {
    Logger() { std::cout << "Logger ctor @" << this << "\n"; }
    void log(const char* msg) { std::cout << "[" << msg << "] @" << this << "\n"; }
};

inline Logger g_logger;
inline Logger& get_logger() { return g_logger; }
```

### libplugin_a.cpp / libplugin_b.cpp
```cpp
#include "logger.hpp"

extern "C" void plugin_a_entry() {
    std::cout << "[A] " << &get_logger() << "\n";
}
```

### main.cpp
```cpp
#include "logger.hpp"

extern "C" void plugin_a_entry();
extern "C" void plugin_b_entry();

int main() {
    std::cout << "[main] " << &get_logger() << "\n";
    plugin_a_entry();
    plugin_b_entry();
}
```

## CMakeLists.txt 概要

```cmake
add_library(plugin_a SHARED libplugin_a.cpp)
add_library(plugin_b SHARED libplugin_b.cpp)

target_include_directories(plugin_a PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(plugin_b PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(dso_scope_demo main.cpp)
target_link_libraries(dso_scope_demo PRIVATE plugin_a plugin_b)
```

## 預期結果

執行 `dso_scope_demo` 後：
```
Logger ctor @0x7f1234...   # main 的
Logger ctor @0x7f5678...   # plugin_a 的
Logger ctor @0x7f9abc...   # plugin_b 的
[main] 0x7f1234...
[A] 0x7f5678...
[B] 0x7f9abc...
```

main、plugin_a、plugin_b 印出**三個不同**位址 → **per-DSO scope**

## 教學重點

1. `inline` variable 在同一個 binary 內保證唯一，但跨 DSO 不保證
2. Dynamic linker 對 `inline` symbol 的處理方式
3. 為什麼 plugin 架構需要特別處理 singleton
4. 這是進入 process_scope 之前的重要鋪墊

---

## Symbol Visibility 深入探討

### 為什麼 Linux Dynamic Linker 不 Merge Inline Symbols？

Linux 的 dynamic linker (`ld.so`) 在載入 DSO 時，對於 **weak symbols**（`inline` 變數會產生 weak symbol）的處理規則：

1. **First definition wins**：第一個被載入的 DSO 的 symbol 會被使用
2. **但前提是 symbol 要 exported**：如果 symbol 被隱藏，就不參與 interposition

問題在於：現代編譯器預設會讓每個 DSO **各自保留一份** inline variable，因為：
- 編譯時不知道其他 DSO 是否有相同 symbol
- 為了避免 ODR violation 風險，各自獨立較安全

### Symbol Visibility 機制

```cpp
// 明確 export（可被其他 DSO 看到）
__attribute__((visibility("default"))) inline Logger g_logger;

// 隱藏（只在本 DSO 內可見）
__attribute__((visibility("hidden"))) inline Logger g_logger;
```

### `-fvisibility=hidden` 編譯選項

```bash
# 預設隱藏所有 symbol，只有明確標記 default 的才 export
g++ -fvisibility=hidden -shared -o libplugin.so plugin.cpp
```

| 設定 | 效果 |
|-----|-----|
| 預設（無 flag） | 大部分 symbol 都 export |
| `-fvisibility=hidden` | 預設隱藏，需明確 export |

### 實驗：讓 Inline Symbol 跨 DSO 共享（不建議）

理論上，如果所有 DSO 都：
1. 使用 `-fvisibility=default`
2. 確保 symbol 是 weak 且 exported
3. 載入順序正確

則 dynamic linker **可能**會 merge 成同一個。但這依賴：
- 載入順序
- Linker 版本
- 編譯器實作細節

**結論**：不可靠，這就是為什麼需要 `process_scope/` 的解法。

### 觀察 Symbol Visibility

```bash
# 查看 DSO 的 exported symbols
nm -D libplugin_a.so | grep logger

# 查看 symbol 的 binding（WEAK/GLOBAL）
readelf -s libplugin_a.so | grep logger
```
