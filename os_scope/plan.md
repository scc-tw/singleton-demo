# os_scope/ — Machine-Level (OS) Singleton Demo

## 目標

展示「整台機器只能有一個 instance」的 singleton，使用 kernel object（lock file + `flock()`）實作。

## 檔案結構

```txt
os_scope/
  CMakeLists.txt
  singleton_daemon.cpp    # 使用 flock 確保單一實例
```

## 核心概念

### singleton_daemon.cpp

```cpp
#include <iostream>
#include <sys/file.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstdlib>

constexpr const char* LOCK_FILE = "/tmp/os_scope_singleton.lock";

int main() {
    int fd = open(LOCK_FILE, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        std::cerr << "Failed to open lock file\n";
        return 1;
    }

    // 嘗試取得 exclusive lock（non-blocking）
    if (flock(fd, LOCK_EX | LOCK_NB) < 0) {
        std::cerr << "Another instance is already running!\n";
        close(fd);
        return 1;
    }

    std::cout << "Singleton daemon started. PID=" << getpid() << "\n";
    std::cout << "Press Enter to exit...\n";

    std::cin.get();

    // Lock 會在 fd close 時自動釋放
    close(fd);
    std::cout << "Daemon exiting.\n";

    return 0;
}
```

## CMakeLists.txt

```cmake
add_executable(os_scope_demo singleton_daemon.cpp)
```

## 預期結果

### 第一個 terminal
```bash
$ ./os_scope_demo
Singleton daemon started. PID=12345
Press Enter to exit...
```

### 第二個 terminal（同時執行）
```bash
$ ./os_scope_demo
Another instance is already running!
```

第二個 process **無法啟動** → **per-machine scope**

## 教學重點

1. **Lock file pattern** 的實作方式
2. `flock()` vs `fcntl()` 的差異
3. `LOCK_NB` (non-blocking) 的用途
4. Lock file 的生命週期管理
5. 與 process_scope/shared_memory 的關係：
   - shared_memory 其實已經是 kernel object，可跨 process
   - 這裡用更簡單的 lock file 展示概念
6. 實際應用場景：
   - Daemon process
   - 避免重複執行的 CLI tool
   - License enforcement

## 延伸討論

可以結合 `process_scope/shared_memory/` 的範例：
- 在另一個 terminal 開第二個 process
- 兩個 process 都呼叫 `get_shm_logger()`
- 證明 shared memory 的 `ProcessLogger` 是跨 process 共享的
- 這就是真正的 **os_scope singleton**（per-machine）

## 進階變體（可選）

1. **Named semaphore**: `sem_open()` 作為跨 process 的 mutex
2. **D-Bus / systemd**: 現代 Linux 的 service 管理方式
3. **Abstract Unix socket**: 不需要檔案系統的 lock 機制
