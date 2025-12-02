# Demo 1: Basic thread_local
add_executable(thread_basic_demo basic_demo.cpp)
target_link_libraries(thread_basic_demo PRIVATE pthread)

# Demo 2: Cross-DSO thread_local
add_library(thread_worker SHARED libworker.cpp)
target_include_directories(thread_worker PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(thread_worker PRIVATE pthread)

add_executable(thread_mixed_demo mixed_demo.cpp)
target_include_directories(thread_mixed_demo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(thread_mixed_demo PRIVATE thread_worker pthread)
