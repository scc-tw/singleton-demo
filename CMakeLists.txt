cmake_minimum_required(VERSION 3.12)
project(singleton_scope_lab CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

add_subdirectory(tu_scope)
# add_subdirectory(dso_scope)
# add_subdirectory(thread_scope)
# add_subdirectory(process_scope)
# add_subdirectory(os_scope)
