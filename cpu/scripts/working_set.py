import re
import subprocess
import time

events = ",".join([
    "FIXED_CYCLES", "FIXED_INSTRUCTIONS", "INST_INT_LD", "INST_SIMD_LD",
    "L1D_CACHE_MISS_LD_NONSPEC", "LDST_UNIT_OLD_L1D_CACHE_MISS",
])
total = 2**30

subprocess.run(["./daxpy", "256", "1", "1"], capture_output=True)
print("W_KiB N repeats time_s cycles instructions IPC cycles_per_access",
      "loads l1d_misses l1d_miss_rate wait_cycles wait_per_miss")
for kib in [4, 16, 32, 64, 256, 1024, 4096, 16384, 65536]:
    n = kib * 1024 // 16
    rep = total // n
    args = ["./daxpy", str(n), str(rep), "1"]
    s = time.perf_counter()
    subprocess.run(args, capture_output=True)
    t = time.perf_counter() - s
    err = subprocess.run(["./mperf", "-e", events, *args],
                         capture_output=True, text=True).stderr
    c = {name: int(val) for val, name in re.findall(r"(\d+)\s+(\w+)", err)}
    cyc, ins = c["FIXED_CYCLES"], c["FIXED_INSTRUCTIONS"]
    loads = c["INST_INT_LD"] + c["INST_SIMD_LD"]
    miss = c["L1D_CACHE_MISS_LD_NONSPEC"]
    wait = c["LDST_UNIT_OLD_L1D_CACHE_MISS"]
    print(kib, n, rep, f"{t:.3f}", cyc, ins, f"{ins / cyc:.2f}",
          f"{cyc / (n * rep):.3f}", loads, miss, f"{100 * miss / loads:.2f}",
          wait, f"{wait / miss:.2f}" if miss else "nan")
