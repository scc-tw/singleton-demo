# ============================================
# Variant 3: dlsym_default
# ============================================
# DSOs use dlsym(RTLD_DEFAULT, ...) to find get_process_logger at runtime.
# This is true late binding - no link-time symbol resolution.

# --- Plugin Libraries (each includes dso_common.cpp) ---
add_library(dlsym_libA SHARED libA.cpp dso_common.cpp)
target_include_directories(dlsym_libA PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(dlsym_libA PRIVATE process_logger_interface dl)

add_library(dlsym_libB SHARED libB.cpp dso_common.cpp)
target_include_directories(dlsym_libB PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(dlsym_libB PRIVATE process_logger_interface dl)

add_library(dlsym_libC SHARED libC.cpp dso_common.cpp)
target_include_directories(dlsym_libC PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(dlsym_libC PRIVATE process_logger_interface dl)

# --- Main executable (owns the singleton) ---
add_executable(dlsym_default_demo main.cpp)
target_link_libraries(dlsym_default_demo
    PRIVATE
    dlsym_libA
    dlsym_libB
    dlsym_libC
    process_logger_interface
    dl
)

# CRITICAL: Export main's symbols so dlsym(RTLD_DEFAULT, ...) can find them
target_link_options(dlsym_default_demo PRIVATE "-Wl,--export-dynamic")
