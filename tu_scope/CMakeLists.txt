add_library(tu_scope_lib
    user_a.cpp
    user_b.cpp
)
target_include_directories(tu_scope_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(tu_scope_demo main.cpp)
target_link_libraries(tu_scope_demo PRIVATE tu_scope_lib)
