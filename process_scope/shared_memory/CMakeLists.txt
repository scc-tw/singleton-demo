# ============================================
# Variant 4: shared_memory
# ============================================
# ProcessLogger lives in POSIX shared memory (kernel object).
# This is a stepping stone to os_scope (cross-process singleton).

# --- Shared library containing shm helper (linked by all) ---
add_library(shm_helper SHARED shm_logger.cpp)
target_include_directories(shm_helper
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
)
target_link_libraries(shm_helper
    PRIVATE process_logger_interface
    PUBLIC rt  # POSIX realtime extensions (shm_open, etc.)
)

# --- Plugin Libraries (all link to shm_helper) ---
add_library(shm_libA SHARED libA.cpp)
target_link_libraries(shm_libA PRIVATE shm_helper process_logger_interface)

add_library(shm_libB SHARED libB.cpp)
target_link_libraries(shm_libB PRIVATE shm_helper process_logger_interface)

add_library(shm_libC SHARED libC.cpp)
target_link_libraries(shm_libC PRIVATE shm_helper process_logger_interface)

# --- Main executable ---
add_executable(shared_memory_demo main.cpp)
target_link_libraries(shared_memory_demo
    PRIVATE
    shm_helper
    shm_libA
    shm_libB
    shm_libC
    process_logger_interface
)
