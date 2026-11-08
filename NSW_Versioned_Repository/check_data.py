

from pathlib import Path
from statistics import mean

raw = Path("data/raw")
arms = {}

for arm, treatment, expected_n in (("treated", 1, 185), ("control", 0, 260)):
    path = raw / f"nswre74_{arm}.txt"
    rows = [
        list(map(float, line.split()))
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]

    assert len(rows) == expected_n, (arm, len(rows), expected_n)
    assert all(len(row) == 10 and row[0] == treatment for row in rows), arm
    arms[arm] = mean(row[9] for row in rows)
    print(f"{arm}: n={len(rows)}, mean RE78={arms[arm]:,.2f}")

print(f"Experimental difference: {arms['treated'] - arms['control']:,.2f}")