"""Command-line interface for csv-merger."""
import argparse
import csv
import os
import sys

from .core import merge, read_csv


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csv-merger", description="Merge CSV files on key columns.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("-k", "--key", required=True, help="comma-separated key column(s)")
    ap.add_argument("--how", choices=["inner", "left", "outer"], default="outer")
    ap.add_argument("-i", "--ignore-case", action="store_true", help="case-insensitive key matching")
    ap.add_argument("--strip-zeros", action="store_true", help="treat 007 and 7 as the same key")
    ap.add_argument("--prefer", choices=["first", "last"], default="first", help="which file wins conflicts")
    ap.add_argument("--source", help="add a column listing the files each row came from")
    ap.add_argument("--conflicts", help="write conflicts to this CSV")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    tables = [(os.path.basename(p),) + read_csv(p) for p in args.files]
    keys = [k.strip() for k in args.key.split(",")]
    header, rows, rep = merge(tables, keys, args.how, args.ignore_case, args.strip_zeros, args.prefer, args.source)
    fh = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    if args.output:
        fh.close()
    err = sys.stderr
    print("%d rows written (%s join of %d files)" % (len(rows), args.how, len(tables)), file=err)
    for name, n in rep["only_in"].items():
        print("  %d key(s) only in %s" % (n, name), file=err)
    for name, k, line in rep["duplicates"][:10]:
        print("  duplicate key %s in %s line %d (ignored)" % ("|".join(k), name, line), file=err)
    if rep["conflicts"]:
        print("  %d conflicting value(s); first kept" % len(rep["conflicts"]), file=err)
        if args.conflicts:
            with open(args.conflicts, "w", newline="", encoding="utf-8") as cf:
                cw = csv.writer(cf)
                cw.writerow(["key", "column", "kept", "other", "source"])
                for c in rep["conflicts"]:
                    cw.writerow(["|".join(c["key"]), c["column"], c["kept"], c["other"], c["source"]])
    return 1 if rep["conflicts"] or rep["duplicates"] else 0
