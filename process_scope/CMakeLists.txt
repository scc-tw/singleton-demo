# process_scope top-level CMakeLists.txt

# Interface library for shared header
add_library(process_logger_interface INTERFACE)
target_include_directories(process_logger_interface
    INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Variant 1: core_shared_lib
add_subdirectory(core_shared_lib)

# Future variants (commented out for now)
# add_subdirectory(main_owner)
# add_subdirectory(dlsym_default)
# add_subdirectory(shared_memory)
