import re
import statistics
import subprocess

events = "FIXED_CYCLES,INST_INT_LD,INST_SIMD_LD,L1D_CACHE_MISS_LD_NONSPEC"
n, rep = 10**7, 20

def measure(repeats, stride):
    args = ["./daxpy", str(n), str(repeats), str(stride)]
    err = subprocess.run(["./mperf", "-e", events, *args],
                         capture_output=True, text=True).stderr
    c = {name: int(val) for val, name in re.findall(r"(\d+)\s+(\w+)", err)}
    loads = c["INST_INT_LD"] + c["INST_SIMD_LD"]
    return c["FIXED_CYCLES"], loads, c["L1D_CACHE_MISS_LD_NONSPEC"]

subprocess.run(["./daxpy", str(n), "0", "1"], capture_output=True)
base = [statistics.median(v) for v in zip(*(measure(0, 1) for _ in range(3)))]
print(f"# baseline (repeats=0): cycles={base[0]:.0f} loads={base[1]:.0f}",
      f"l1d_misses={base[2]:.0f}")
print("stride N_access cycles cycles_per_access loads l1d_misses l1d_miss_rate")
for s in [1, 2, 4, 8, 16, 32, 64]:
    acc = n // s * rep
    cyc, loads, miss = (a - b for a, b in zip(measure(rep, s), base))
    print(s, acc, round(cyc), f"{cyc / acc:.2f}", round(loads), round(miss),
          f"{100 * miss / loads:.2f}")
