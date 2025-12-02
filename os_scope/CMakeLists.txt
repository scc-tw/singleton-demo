# ============================================
# os_scope: Machine-Level Singleton
# ============================================
# Uses flock() + lock file to ensure only ONE instance
# can run on the entire machine.

add_executable(os_scope_demo singleton_daemon.cpp)
