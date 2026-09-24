import plistlib

with open("/usr/share/kpep/as3.plist", "rb") as f:
    events = plistlib.load(f)["system"]["cpu"]["events"]
for name, event in sorted(events.items()):
    print(name.ljust(36), event.get("description", ""))
