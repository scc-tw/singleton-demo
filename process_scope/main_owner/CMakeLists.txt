# ============================================
# Variant 2: main_owner
# ============================================
# Singleton defined in main executable.
# DSOs find it via --export-dynamic linker flag.

# --- Plugin Libraries (only declare extern, no definition) ---
add_library(main_owner_libA SHARED libA.cpp)
target_link_libraries(main_owner_libA PRIVATE process_logger_interface)

add_library(main_owner_libB SHARED libB.cpp)
target_link_libraries(main_owner_libB PRIVATE process_logger_interface)

add_library(main_owner_libC SHARED libC.cpp)
target_link_libraries(main_owner_libC PRIVATE process_logger_interface)

# --- Main executable (owns the singleton) ---
add_executable(main_owner_demo main.cpp)
target_link_libraries(main_owner_demo
    PRIVATE
    main_owner_libA
    main_owner_libB
    main_owner_libC
    process_logger_interface
)

# CRITICAL: Export main's symbols so DSOs can find get_process_logger()
target_link_options(main_owner_demo PRIVATE "-Wl,--export-dynamic")
