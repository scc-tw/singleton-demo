# tu_scope/ — Translation Unit Level Singleton Demo

## 目標

展示 `static` vs `inline` variable 在多個 `.cpp` 裡的差異：
- **per-TU**：每個 translation unit 各有一份（non-inline static）
- **per-binary**：整個執行檔只有一份（inline variable）

## 檔案結構

```txt
tu_scope/
  CMakeLists.txt
  logger.hpp            # Logger class 定義
  logger_static.cpp     # non-inline static，每個 TU 一份
  logger_inline.hpp     # inline variable 版，整個 binary 一份
  user_a.cpp            # 呼叫 static & inline 版印位址
  user_b.cpp            # 呼叫 static & inline 版印位址
  main.cpp              # 比較位址差異
```

## 核心概念

### 什麼是 ODR (One Definition Rule)？

ODR 是 C++ 的核心規則，簡單來說：
1. **Per TU**：一個變數/函式在一個 Translation Unit 內只能定義一次。
2. **Per Program**：如果一個變數/函式被多個 TU 使用（external linkage），整個程式中只能有**唯一**的定義。

*   **Violating ODR**: 如果在 header 寫 `int g_count;`（無 `static`/`inline`），被兩個 .cpp include，Linker 會報錯 "multiple definition"。
*   **Avoiding ODR (Old way)**: 使用 `static`（Internal Linkage）。雖然避開了 Linker Error，但創造了多個獨立實體，破壞 Singleton 語意。
*   **Solving ODR (Modern way)**: 使用 `inline`（C++17）。允許在 Header 定義，由 Compiler/Linker 保證全程式唯一。

### logger.hpp
定義 `Logger` class，可以印出 `this` 位址。

### logger_static.cpp
```cpp
static Logger g_logger_static;  // 每個 include 的 TU 都會有自己的一份
Logger& get_logger_static() { return g_logger_static; }
```

### logger_inline.hpp
```cpp
inline Logger g_logger_inline;  // C++17，整個 binary 只有一份
inline Logger& get_logger_inline() { return g_logger_inline; }
```

## 預期結果

執行 `tu_scope_demo` 後：
- `get_logger_static()` 在 user_a 和 user_b 印出**不同**位址（per-TU）
- `get_logger_inline()` 在 user_a 和 user_b 印出**相同**位址（per-binary）

## CMakeLists.txt 概要

```cmake
add_library(tu_scope_lib
    logger_static.cpp
    user_a.cpp
    user_b.cpp
)

add_executable(tu_scope_demo main.cpp)
target_link_libraries(tu_scope_demo PRIVATE tu_scope_lib)
```

## 教學重點

1. `static` 變數在 header 的陷阱
2. C++17 `inline` variable 解決 ODR 問題
3. Translation Unit 的定義與邊界
