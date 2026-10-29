import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from csv_merger.cli import main
from csv_merger.core import merge

A = ("a.csv", ["id", "age", "site"], [{"id": "001", "age": "30", "site": "N"}, {"id": "2", "age": "", "site": "S"},
                                       {"id": "3", "age": "50", "site": "S"}, {"id": "3", "age": "51", "site": "S"}])
B = ("b.csv", ["id", "age", "score"], [{"id": "1", "age": "31", "score": "7"}, {"id": "2", "age": "44", "score": "9"},
                                        {"id": "4", "age": "60", "score": "5"}])


class MergeTests(unittest.TestCase):
    def test_outer_with_zero_stripping(self):
        header, rows, rep = merge([A, B], ["id"], strip_zeros=True, source_col="_from")
        self.assertEqual(header, ["id", "age", "site", "score", "_from"])
        by = {r["id"]: r for r in rows}
        self.assertEqual(len(rows), 4)
        self.assertEqual(by["001"]["score"], "7")
        self.assertEqual(by["2"]["age"], "44")           # empty filled from the other file
        self.assertEqual(by["001"]["_from"], "a.csv;b.csv")

    def test_conflicts_and_duplicates(self):
        _, _, rep = merge([A, B], ["id"], strip_zeros=True)
        self.assertEqual([(c["column"], c["kept"], c["other"]) for c in rep["conflicts"]], [("age", "30", "31")])
        self.assertEqual(rep["duplicates"], [("a.csv", ("3",), 5)])

    def test_prefer_last(self):
        _, rows, _ = merge([A, B], ["id"], strip_zeros=True, prefer="last")
        self.assertEqual({r["id"]: r["age"] for r in rows}["1"], "31")

    def test_join_types(self):
        self.assertEqual(len(merge([A, B], ["id"], "inner")[1]), 1)                # only id 2 without zero stripping
        self.assertEqual(len(merge([A, B], ["id"], "inner", strip_zeros=True)[1]), 2)
        self.assertEqual(sorted(r["id"] for r in merge([A, B], ["id"], "left")[1]), ["001", "2", "3"])
        with self.assertRaises(ValueError):
            merge([A, B], ["id"], "cross")

    def test_missing_key_column(self):
        with self.assertRaises(ValueError):
            merge([A, ("c.csv", ["x"], [])], ["id"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p1, p2, out, cf = (os.path.join(d, n) for n in ("a.csv", "b.csv", "m.csv", "c.csv"))
            with open(p1, "w", encoding="utf-8") as fh:
                fh.write("ID,x\nab,1\n")
            with open(p2, "w", encoding="utf-8") as fh:
                fh.write("ID,x,y\nAB,2,3\n")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main([p1, p2, "-k", "ID", "-i", "-o", out, "--conflicts", cf]), 1)
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(fh.read().splitlines(), ["ID,x,y", "ab,1,3"])
            self.assertTrue(os.path.exists(cf))


if __name__ == "__main__":
    unittest.main()
