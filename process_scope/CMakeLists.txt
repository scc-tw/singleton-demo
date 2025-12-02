# process_scope top-level CMakeLists.txt

# Interface library for shared header
add_library(process_logger_interface INTERFACE)
target_include_directories(process_logger_interface
    INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Variant 1: core_shared_lib
add_subdirectory(core_shared_lib)

# Variant 2: main_owner
add_subdirectory(main_owner)

# Variant 3: dlsym_default
add_subdirectory(dlsym_default)

# Variant 4: shared_memory
add_subdirectory(shared_memory)
