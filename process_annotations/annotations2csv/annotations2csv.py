#!/usr/bin/env python
#  -*- coding: utf-8 -*-


import os
import argparse
import pathlib
from builtins import set

import regex
import intervaltree as itree
import itertools
import csv
from typing import TypeVar, Dict, Tuple, NamedTuple, Iterator, List, Set

# typing declarations
IntervalTree = TypeVar('IntervalTree', bound=itree.IntervalTree)
Interval = TypeVar('Interval', bound=itree.Interval)
Namespace = TypeVar('Namespace', bound=argparse.Namespace)
AnnType = str
AnnDifficulty = str
Filename = str

# custom type
AnnotatedLine = NamedTuple('AnnotatedLine', [('line_num', int),
                                             ('types', Set[AnnType]),
                                             ('text', str)])
Annotations = List[AnnotatedLine]
AnnotationData = NamedTuple('AnnotationData',
                            [('annotation_difficulty', AnnType),
                             ('annotations', Annotations)])
AnnotatedFiles = Dict[Filename, AnnotationData]

# matches the annotation type, and all the beginning/ending offsets
PATTERN_ANN = \
    regex.compile(r'\t(?P<type>.+) ((?P<begin>\d+) (?P<end>\d+);?)+\t')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Generates a CSV file with '
                    ' this format: [filename,line number,'
                    ' annotation type(s),text]'
                    ' (annotations are separated by spaces)')
    parser.add_argument('dir_base', nargs='?', default='.', type=str,
                        help='directory read recursively '
                             'to process *.ann and *.txt files.'
                             ' Default value: current directory.'
                             'Pairs of files .ann and .txt are expected'
                             ' to be in the same directory.'
                        )
    parser.add_argument('-o', '--out', dest='file_csv', type=str,
                        default='annotations.csv',
                        help='Output CSV file.')
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true',
                        help='Displays the (full) name of the files read.')
    args: argparse.Namespace = parser.parse_args()

    return args


def get_interval_ann(match) -> Tuple[int, int, set]:
    """Return a Interval corresponding to the 'match' pattern, using the min
    and max of all the intervals"""

    anns_type: Set = match.captures('type')[0]
    anns_begin: int = min(map(int, match.captures('begin')))
    anns_end: int = max(map(int, match.captures('end')))

    return anns_begin, anns_end, anns_type


def parse_annotations(filename: str, pattern) -> IntervalTree:
    """Return an ``IntervalTree`` for the annotations contained in this file
    (empty if there's an error).
    pattern: regex used to parse each line of annotation."""

    interval_tree: IntervalTree = itree.IntervalTree()

    try:
        with open(filename, 'r') as f:
            interval_tree = itree.IntervalTree()

            for line in f:
                parsed_ann = pattern.search(line)
                if parsed_ann:
                    interval_tree.addi(*get_interval_ann(parsed_ann))
    except OSError as error:
        print(f'✘ Error while parsing {filename}:\n{error}')

    return interval_tree


def get_interval_offsets_txt(lines: List[str]) -> Iterator[Tuple[int, int]]:
    """Return all the intervals corresponding to the ``lines``
    passed as parameter:
    [(0, n), (n, m), …]
    where the values are the character position of the beginning and end of
    each line, counting from the first character of the file (start at 0)"""

    idx_first_char = 0
    cumulative_lines_length = list(itertools.accumulate(list(map(len, lines))))

    return zip([idx_first_char] + cumulative_lines_length,
               cumulative_lines_length)


def parse_text(filename: str) -> IntervalTree:
    """Return an ``IntervalTree`` for this file (empty if there's an error)"""

    try:
        with open(filename, 'r') as ftxt:
            # skip the 5 last lines, used for controlling the annotation

            return itree.IntervalTree.from_tuples(
                get_interval_offsets_txt(ftxt.readlines()))
    except OSError as error:
        print(f'✘ Error while parsing {filename}:\n{error}')

        return itree.IntervalTree()


def annotate_txt(annotations: AnnotatedFiles,
                 file_text: Filename, nb_lines_skipped: int,
                 interval_tree_ann: IntervalTree,
                 interval_tree_txt: IntervalTree,
                 no_type: AnnType) -> None:
    """Modify ``annotations``: adds annotations of ``file_text``, using the
    annotations and text intervals.
    When no annotation exists, the annotation type is set to ``no_type``"""

    ord_interval_tree_txt: List[IntervalTree] = sorted(interval_tree_txt)
    annotations[file_text] = AnnotationData(annotation_difficulty=no_type,
                                            annotations=[])

    try:
        # virtual line: line created when a line is splited for Brat because it
        # is too long. This is the format for the *.txt
        # the line number is kept for debugging

        with open(file_text, 'r') as ftxt:
            idx_raw: int = 0
            idx_line: int = 1

            # it is OK to read all the lines because
            # the files are small (< 500KB)
            all_lines = ftxt.readlines()
            for line in all_lines:
                types = get_types(idx_raw, interval_tree_ann, no_type,
                                  ord_interval_tree_txt)
                # anns: Annotations =
                annotations[file_text].annotations.append(
                    AnnotatedLine(line_num=idx_line,
                                  types=types,
                                  text=line.rstrip()))
                # annotations[file_text]._replace(annotations=anns)

                idx_raw += 1
                idx_line += 1

            # the last line of the .txt file is blank,
            # the difficulty is the line at position -2
            ann_difficulty: AnnType = annotations[file_text].annotations[
                -2].types.pop()
            idx_max_line_kept: int = len(all_lines) - nb_lines_skipped
            annotations[file_text] = AnnotationData(
                annotation_difficulty=ann_difficulty,
                annotations=list(itertools.takewhile(
                    lambda ann_line: ann_line.line_num < idx_max_line_kept,
                    annotations[file_text].annotations)))
    except OSError as error:
        print(f'✘ Error while annotating {file_text}:\n{error}')


def get_types(idx_raw: int, interval_tree_ann: IntervalTree,
              no_type: AnnType, ord_interval_tree_txt: List[IntervalTree]) -> \
        Set[AnnType]:
    # types for overlapping intervals
    maybe_types: Set[itree.Interval] = interval_tree_ann.search(
        ord_interval_tree_txt[idx_raw])
    types: Set[AnnType] = {t.data for t in maybe_types} \
        if len(maybe_types) != 0 else {no_type}

    return types


def merge_txt(raw_ann: AnnotationData, no_type: AnnType) -> AnnotationData:
    """
    Return a normalized (lines merged) version of ``raw_ann``:
    '\n\n' in *.txt are the real lines, and are parsed as ''.
    So to create real lines, we merge all the strings between ''.
    """

    merged_ann: AnnotationData = AnnotationData(
        annotation_difficulty=raw_ann.annotation_difficulty,
        annotations=[])
    types: Set = set()
    lines: List[str] = []
    i: int = 0

    for virtual_line in raw_ann.annotations:
        if virtual_line.text == '':
            i += 1
            # remove no_type from the virtual lines when part of the line was
            # annotated
            if len(types) > 1:
                types.discard(no_type)
            merged_ann.annotations.append(AnnotatedLine(line_num=i,
                                                        types=types,
                                                        text=' '.join(lines)))
            types = set()
            lines = []
        else:
            types |= virtual_line.types
            lines.append(virtual_line.text)

    return merged_ann


def main():
    # Generate a CSV file:
    # - Processes recursively all the annotations (.ann) and text (.txt) files
    # in the data directory given as a parameter.

    args: Namespace = parse_args()

    file_csv: str = args.file_csv
    dir_base: pathlib.Path = pathlib.Path(args.dir_base).resolve()

    no_type: AnnType = 'n_a'
    annotations: AnnotatedFiles = dict()
    merged_ann: AnnotatedFiles = dict()
    # skip the 5 last lines, used to evaluate the difficulty of the annotation
    nb_lines_skipped = 5  # type: int
    stat_nb_files = 0  # type: int
    stat_nb_files_skipped = 0  # type: int

    print(f'Processing: "{dir_base}"')
    for file_ann in dir_base.glob('**/*.ann'):
        if args.verbose:
            print(file_ann)

        if os.stat(file_ann).st_size == 0:  # empty when not annotated
            stat_nb_files_skipped += 1
            if args.verbose:
                print('✘ File is empty, skipped.')
        else:
            stat_nb_files += 1

            # IntervalTree allows to find character number intervals (from
            # annotations) that intersect character number intervals of a line
            # (from the original text)
            interval_tree = parse_annotations(file_ann, PATTERN_ANN)

            file_text = os.path.splitext(file_ann)[0] + '.txt'
            interval_tree_txt = parse_text(file_text)

            # maps each line of .txt with the annotation type(s)
            annotate_txt(annotations, file_text,
                         nb_lines_skipped,
                         interval_tree,
                         interval_tree_txt,
                         no_type)
            # Now convert this "raw" annotated text to the original text format
            merged_ann[file_text] = merge_txt(annotations[file_text], no_type)

            if args.verbose:
                print('✓')

    print(
        f'{stat_nb_files} annotation(s) files processed successfully;'
        f' {stat_nb_files_skipped} skipped (empty).')

    # write the CSV
    try:
        with open(file_csv, 'w', newline='') as c:
            writer = csv.writer(c, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(
                ['filename', 'line_num', 'types', 'annotation_difficulty',
                 'text'])
            for filename in merged_ann:
                annotation_difficulty = merged_ann[
                    filename].annotation_difficulty
                for ann in merged_ann[filename].annotations:
                    writer.writerow(
                        [filename, ann.line_num, ' '.join(ann.types),
                         annotation_difficulty,
                         ann.text])
        print(f'Result in "{file_csv}"')
    except OSError as error:
        print(f'✘ Error while writing {file_csv}:\n{error}')


if __name__ == '__main__':
    main()
