# tu_scope/ — Translation Unit Level Singleton Demo

## 目標

展示 `static` vs `inline` variable 在多個 `.cpp` 裡的差異：
- **per-TU**：每個 translation unit 各有一份（header 中的 static）
- **per-binary**：整個執行檔只有一份（inline variable）

## 檔案結構

```txt
tu_scope/
  CMakeLists.txt
  logger.hpp            # Logger class 定義
  logger_static.hpp     # static variable 版（陷阱示範）
  logger_inline.hpp     # inline variable 版（正確做法）
  user_a.cpp            # TU A：印出 static & inline 位址
  user_b.cpp            # TU B：印出 static & inline 位址
  main.cpp              # Entry point
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

### logger_static.hpp（陷阱示範）
```cpp
// WARNING: 每個 include 這個 header 的 TU 都會有自己的 g_logger_static
static Logger g_logger_static;

static Logger& get_logger_static() {
    return g_logger_static;
}
```

### logger_inline.hpp（正確做法）
```cpp
// C++17：整個 binary 只有一份
inline Logger g_logger_inline;

inline Logger& get_logger_inline() {
    return g_logger_inline;
}
```

## 預期結果

執行 `tu_scope_demo` 後：

```
=== TU Scope Singleton Demo ===

Logger ctor @0x...AAA   # user_a 的 static
Logger ctor @0x...BBB   # user_a 的 inline (第一次)
[user_a] static:  0x...AAA
[user_a] inline:  0x...BBB

Logger ctor @0x...CCC   # user_b 的 static (不同！)
[user_b] static:  0x...CCC
[user_b] inline:  0x...BBB   # 同一個！

=== Expected Result ===
static:  user_a != user_b (per-TU)
inline:  user_a == user_b (per-binary)
```

- `get_logger_static()` 在 user_a 和 user_b 印出**不同**位址（per-TU）
- `get_logger_inline()` 在 user_a 和 user_b 印出**相同**位址（per-binary）

## CMakeLists.txt

```cmake
add_library(tu_scope_lib
    user_a.cpp
    user_b.cpp
)
target_include_directories(tu_scope_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(tu_scope_demo main.cpp)
target_link_libraries(tu_scope_demo PRIVATE tu_scope_lib)
```

## 教學重點

1. `static` 變數在 header 的陷阱
2. C++17 `inline` variable 解決 ODR 問題
3. Translation Unit 的定義與邊界

## 對比表

| 類型 | Header 寫法 | 結果 | 說明 |
|-----|------------|------|-----|
| `static` | `static Logger g;` | 每 TU 各一份 | Internal linkage，各 TU 獨立 |
| `inline` | `inline Logger g;` | 整個 binary 一份 | C++17 ODR 解決方案 |
