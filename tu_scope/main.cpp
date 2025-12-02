#include <iostream>

void user_a_report();
void user_b_report();

int main() {
    std::cout << "=== TU Scope Singleton Demo ===\n\n";

    user_a_report();
    std::cout << "\n";
    user_b_report();

    std::cout << "\n=== Expected Result ===\n";
    std::cout << "static:  user_a != user_b (per-TU)\n";
    std::cout << "inline:  user_a == user_b (per-binary)\n";

    return 0;
}
