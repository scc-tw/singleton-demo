# ============================================
# Variant 1: core_shared_lib
# ============================================
# All DSOs link to a central "core" library that owns the singleton.

# --- The Core Library (owns the singleton) ---
add_library(process_core SHARED core_api.cpp)
target_link_libraries(process_core PRIVATE process_logger_interface)
target_include_directories(process_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# --- Plugin Libraries (link to core) ---
add_library(process_libA SHARED libA.cpp)
target_link_libraries(process_libA PRIVATE process_core process_logger_interface)

add_library(process_libB SHARED libB.cpp)
target_link_libraries(process_libB PRIVATE process_core process_logger_interface)

add_library(process_libC SHARED libC.cpp)
target_link_libraries(process_libC PRIVATE process_core process_logger_interface)

# --- Main executable (links to core + plugins) ---
add_executable(process_core_demo main.cpp)
target_link_libraries(process_core_demo
    PRIVATE
    process_core
    process_libA
    process_libB
    process_libC
    process_logger_interface
)
