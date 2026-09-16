"""Throwaway: regex window search over a text file. usage: file pattern [window] [max]"""
import re
import sys

if __name__ == "__main__":
    path, pat = sys.argv[1], sys.argv[2]
    win = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    mx = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    t = open(path).read()
    n = 0
    for m in re.finditer(pat, t, flags=re.I):
        s, e = max(0, m.start() - win), min(len(t), m.end() + win)
        print("---[%d]--- %s" % (m.start(), t[s:e]))
        n += 1
        if n >= mx:
            break
    if n == 0:
        print("NO MATCH for", pat)
