# Plugin A shared library
add_library(dso_plugin_a SHARED libplugin_a.cpp)
target_include_directories(dso_plugin_a PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
# Hide symbols by default - this prevents symbol merging across DSOs
target_compile_options(dso_plugin_a PRIVATE -fvisibility=hidden)

# Plugin B shared library
add_library(dso_plugin_b SHARED libplugin_b.cpp)
target_include_directories(dso_plugin_b PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_options(dso_plugin_b PRIVATE -fvisibility=hidden)

# Main executable
add_executable(dso_scope_demo main.cpp)
target_link_libraries(dso_scope_demo PRIVATE dso_plugin_a dso_plugin_b)
