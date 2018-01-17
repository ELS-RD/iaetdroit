# annotation2csv

## Description
Read Brat annotation files and the associated text files, and generates a CSV
containing the text lines and their annotations.

Note: some line breaks are removed from the text files, when they were
introduced to ease the annotation in Brat (lines ≤ 80 characters),
so the line count is different in the CSV than the original file.

## Requirements
Tested with:

* python ≥ 3.6
* GNU/Linux

## Typing
You can check the typing with:

`mypy --ignore-missing-imports annotations2csv/annotations2csv.py`

## Example
* To see how the program works, execute `./run.sh`.
It reads files from the sample `data` directory.
* To process all the files of the dataset, we used:
`python annotations2csv/annotations2csv.py  /some-input-dir/brat_6-12 -o /some-output-dir/annotations.csv`
