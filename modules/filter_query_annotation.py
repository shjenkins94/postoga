#!/usr/bin/env python3


""" A module to filter the original .bed file based on the query table."""


import pandas as pd
import os
from constants import Constants
from logger import Log


__author__ = "Alejandro Gonzales-Irribarren"
__email__ = "jose.gonzalesdezavala1@unmsm.edu.pe"
__github__ = "https://github.com/alejandrogzi"
__version__ = "0.5.0-devel"


def filter_bed(
    path: str, table: pd.DataFrame, by_class: list, by_rel: list, threshold: str
) -> str:
    """
    Filters the original .bed file to produce a custom filtered file

    @type path: str
    @param path: path to the directory where the files will be written
    @type log: Log
    @param log: logger object to record messages
    @type table: pd.DataFrame
    @param table: a pandas DataFrame
    @param threshold: Threshold for filtering
    @param by_class: Filter by class
    @param by_rel: Filter by relation
    """

    log = Log.connect(path, Constants.FileNames.LOG)
    initial = len(table)

    if threshold:
        table = table[table["pred"] >= float(threshold)]
        log.record(
            f"discarded {initial - len(table)} projections with orthology scores <{threshold}"
        )

    if by_class:
        edge = len(table)
        table = table[table["class"].isin(by_class.split(","))]
        log.record(
            f"discarded {edge - len(table)} projections with classes other than {by_class}"
        )

    if by_rel:
        edge = len(table)
        table = table[table["relation"].isin(by_rel.split(","))]
        log.record(
            f"discarded {edge - len(table)} projections with relationships other than {by_rel}"
        )

    # Read the original .bed file and filter it based on the transcripts table
    bed = pd.read_csv(
        os.path.join(path, Constants.FileNames.BED), sep="\t", header=None
    )
    bed = bed[bed[3].isin(table["transcripts"])]
    custom_table = table[table["transcripts"].isin(bed[3])]

    # Write the filtered .bed file
    f = os.path.join(path, Constants.FileNames.FILTERED_BED)
    bed.to_csv(
        f,
        sep="\t",
        header=None,
        index=False,
    )

    info = [
        f"kept {len(bed)} projections after filters, discarded {initial - len(bed)}.",
        f"{len(bed)} projections are coming from {len(custom_table['helper'].unique())} unique transcripts and {len(custom_table['t_gene'].unique())} genes",
        f"class stats of new bed: {custom_table['class'].value_counts().to_dict()}",
        f"relation stats of new bed: {custom_table['relation'].value_counts().to_dict()}",
        f"confidence stats of new bed: {custom_table['confidence_level'].value_counts().to_dict()}",
        f"filtered bed file written to {f}",
    ]

    [log.record(i) for i in info]

    return f