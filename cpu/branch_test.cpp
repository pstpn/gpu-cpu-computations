#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

int main(int argc, char** argv) {
  if (argc != 4) {
    fprintf(stderr, "usage: %s <mode: 0 - predictable, 1 - random> <n> <repeats>\n", argv[0]);
    return 1;
  }
  int    mode    = std::atoi(argv[1]);
  size_t n       = std::atoll(argv[2]);
  size_t repeats = std::atoll(argv[3]);

  std::vector<uint8_t> cond(n);
  std::vector<int> data(n);
  std::mt19937 gen(42);
  for (size_t i = 0; i < n; i++) {
    uint8_t random_bit = gen() & 1;
    cond[i] = mode == 0 ? i < n / 2 : random_bit;
    data[i] = i & 0xff;
  }

  long long sum = 0;
  for (size_t r = 0; r < repeats; r++) {
    for (size_t i = 0; i < n; i++) {
      if (cond[i]) {
        sum += data[i];
      }
    }
  }

  printf("checksum : %lld\n", sum);
  return 0;
}
