#include "libworker.hpp"
#include "thread_logger.hpp"

void call_logger_in_lib(const char* context) {
    get_thread_logger().log(context);
}
