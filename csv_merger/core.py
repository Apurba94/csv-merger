"""Join tables on keys (inner/left/outer), reconcile overlapping columns and report problems."""
import csv


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames or []), list(r)


def _norm_key(row, keys, case_insensitive, strip_zeros):
    vals = []
    for k in keys:
        v = (row.get(k) or "").strip()
        if case_insensitive:
            v = v.lower()
        if strip_zeros and v.isdigit():
            v = v.lstrip("0") or "0"
        vals.append(v)
    return tuple(vals)


def merge(tables, keys, how="outer", case_insensitive=False, strip_zeros=False, prefer="first", source_col=None):
    """Merge a list of (name, header, rows) tables on `keys`.

    Overlapping non-key columns are combined: empty values are filled from other tables; when two
    tables disagree, `prefer` ('first' or 'last') decides and a conflict is recorded.
    Returns (header, rows, report) where report has duplicates, conflicts, unmatched counts.
    """
    report = {"duplicates": [], "conflicts": [], "only_in": {}, "missing_key_columns": []}
    header = list(keys)
    indexed = []
    for name, h, rows in tables:
        missing = [k for k in keys if k not in h]
        if missing:
            report["missing_key_columns"].append((name, missing))
            continue
        for c in h:
            if c not in header:
                header.append(c)
        idx = {}
        for i, r in enumerate(rows, start=2):
            k = _norm_key(r, keys, case_insensitive, strip_zeros)
            if not any(k):
                continue
            if k in idx:
                report["duplicates"].append((name, k, i))
                continue
            idx[k] = r
        indexed.append((name, idx))
    if report["missing_key_columns"]:
        raise ValueError("key column(s) missing: %s" % report["missing_key_columns"])
    key_sets = [set(idx) for _, idx in indexed]
    if how == "inner":
        all_keys = set.intersection(*key_sets) if key_sets else set()
    elif how == "left":
        all_keys = key_sets[0] if key_sets else set()
    elif how == "outer":
        all_keys = set.union(*key_sets) if key_sets else set()
    else:
        raise ValueError("how must be inner, left or outer")
    first_seen = []
    for _, idx in indexed:
        for k in idx:
            if k in all_keys and k not in first_seen:
                first_seen.append(k)
    first_seen_set = set(first_seen)
    first_seen += sorted(all_keys - first_seen_set)
    for name, idx in indexed:
        report["only_in"][name] = sum(1 for k in idx if all(k not in other for n2, other in indexed if n2 != name))
    order = indexed if prefer == "first" else list(reversed(indexed))
    out = []
    for k in first_seen:
        row = {}
        present = []
        for name, idx in order:
            r = idx.get(k)
            if r is None:
                continue
            present.append(name)
            for c, v in r.items():
                v = (v or "").strip()
                if c in keys:
                    row.setdefault(c, v)
                    continue
                if not row.get(c):
                    row[c] = v
                elif v and v != row[c]:
                    report["conflicts"].append({"key": k, "column": c, "kept": row[c], "other": v, "source": name})
        if source_col:
            row[source_col] = ";".join(sorted(present))
        out.append(row)
    if source_col and source_col not in header:
        header.append(source_col)
    return header, out, report
