# csv-merger

**Merge spreadsheets from different sources on participant/sample IDs, with explicit reporting
of duplicates, unmatched records and conflicting values instead of silent overwrites.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Combining lab results with questionnaire data, or site A with site B, is where many data errors
are born: IDs written `007` vs `7`, `ab12` vs `AB12`, the same participant twice, two files that
disagree on age. Spreadsheet VLOOKUPs fail silently. `csv-merger` performs the join and tells you
everything that did not line up.

## Features

- Inner, left and outer joins on one or more key columns, any number of files
- Key normalization: whitespace, `--ignore-case`, `--strip-zeros`
- Overlapping columns are reconciled: empty values filled from other files, disagreements
  recorded as conflicts (`--prefer first|last`), exportable to CSV
- Reports duplicate keys (with line numbers) and keys found in only one file
- `--source` provenance column; exit code 1 if conflicts or duplicates were found

## Usage

```bash
pip install .
csv-merger labs.csv survey.csv -k participant_id --strip-zeros -o merged.csv
csv-merger site_a.csv site_b.csv -k id,visit --how inner --source _file --conflicts conflicts.csv
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
