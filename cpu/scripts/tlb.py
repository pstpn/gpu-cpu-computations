import re
import statistics
import subprocess

events = "FIXED_CYCLES,L1D_TLB_ACCESS,L1D_TLB_MISS,L2_TLB_MISS_DATA"
total = 2**24

def measure(n, repeats):
    args = ["./daxpy", str(n), str(repeats), "2048"]
    err = subprocess.run(["./mperf", "-e", events, *args],
                         capture_output=True, text=True).stderr
    c = {k: int(v) for v, k in re.findall(r"(\d+)\s+(\w+)", err)}
    return [c[e] for e in events.split(",")]

subprocess.run(["./daxpy", "1024", "1", "2048"], capture_output=True)
print("pages N repeats N_access cycles cycles_per_access",
      "l1_dtlb_accesses l1_dtlb_misses l1_dtlb_miss_rate l2_tlb_misses")
for k in range(17, 26):
    n = 2**k
    rep = total // (n // 2048)
    base = [statistics.median(v) for v in zip(*(measure(n, 0) for _ in range(3)))]
    cyc, acc_tlb, miss1, miss2 = (a - b for a, b in zip(measure(n, rep), base))
    acc = n // 2048 * rep
    print(n // 1024, n, rep, acc, round(cyc), f"{cyc / acc:.2f}", round(acc_tlb),
          round(miss1), f"{100 * miss1 / acc_tlb:.2f}", round(miss2))
