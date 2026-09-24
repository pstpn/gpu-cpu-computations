import re
import statistics
import subprocess
import time

events = "FIXED_CYCLES,INST_BRANCH,BRANCH_MISPRED_NONSPEC"
n, rep = 10**6, 100

def measure(mode, repeats):
    args = ["./branch_test", str(mode), str(n), str(repeats)]
    times = []
    for _ in range(3):
        s = time.perf_counter()
        subprocess.run(args, capture_output=True)
        times.append(time.perf_counter() - s)
    err = subprocess.run(["./mperf", "-e", events, *args],
                         capture_output=True, text=True).stderr
    c = {k: int(v) for v, k in re.findall(r"(\d+)\s+(\w+)", err)}
    return [statistics.median(times)] + [c[e] for e in events.split(",")]

subprocess.run(["./branch_test", "0", "1000", "1"], capture_output=True)
print("mode time_s cycles branches branch_misses branch_miss_rate")
for mode, name in [(0, "predictable"), (1, "random")]:
    t, cyc, br, miss = (a - b for a, b in zip(measure(mode, rep), measure(mode, 0)))
    print(name, f"{t:.3f}", cyc, br, miss, f"{100 * miss / br:.2f}")
