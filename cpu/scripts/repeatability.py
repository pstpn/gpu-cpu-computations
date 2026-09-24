import re
import statistics as st
import subprocess
import time

args = ["./daxpy", "1000000", "100", "1"]
subprocess.run(args, capture_output=True)
t, cyc, ins = [], [], []
for _ in range(10):
    s = time.perf_counter()
    subprocess.run(args, capture_output=True)
    t.append(time.perf_counter() - s)
    err = subprocess.run(["/usr/bin/time", "-l", *args],
                         capture_output=True, text=True).stderr
    cyc.append(int(re.search(r"(\d+)\s+cycles elapsed", err)[1]))
    ins.append(int(re.search(r"(\d+)\s+instructions retired", err)[1]))
for name, v in [("time, s", t), ("cycles", cyc), ("instructions", ins)]:
    m, s = st.mean(v), st.stdev(v)
    print(f"{name:13} {m:.6g} +- {100 * s / m:.2f}%")
