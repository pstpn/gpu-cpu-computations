import re
import subprocess
import time

events = ",".join([
    "FIXED_CYCLES", "INST_INT_LD", "INST_SIMD_LD",
    "L1D_CACHE_MISS_LD_NONSPEC", "LDST_UNIT_OLD_L1D_CACHE_MISS",
])
total = 2**30
types = [("./daxpy_float", "float", 4), ("./daxpy", "double", 8)]

print("N repeats type W_KiB time_s cycles cycles_per_access",
      "loads l1d_misses l1d_miss_rate wait_per_miss")
for n in [4096, 12288, 1572864]:
    rep = total // n
    for binary, name, size in types:
        args = [binary, str(n), str(rep), "1"]
        subprocess.run(args, capture_output=True)
        s = time.perf_counter()
        subprocess.run(args, capture_output=True)
        t = time.perf_counter() - s
        err = subprocess.run(["./mperf", "-e", events, *args],
                             capture_output=True, text=True).stderr
        c = {k: int(v) for v, k in re.findall(r"(\d+)\s+(\w+)", err)}
        cyc, loads = c["FIXED_CYCLES"], c["INST_INT_LD"] + c["INST_SIMD_LD"]
        miss = c["L1D_CACHE_MISS_LD_NONSPEC"]
        wait = c["LDST_UNIT_OLD_L1D_CACHE_MISS"]
        print(n, rep, name, 2 * n * size // 1024, f"{t:.3f}", cyc,
              f"{cyc / (n * rep):.3f}", loads, miss, f"{100 * miss / loads:.2f}",
              f"{wait / miss:.2f}" if miss else "nan")
