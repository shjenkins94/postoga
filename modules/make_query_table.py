#!/usr/bin/env python3

""" Module to create a query table directly from a TOGA output. """


import os
import pandas as pd
from constants import Constants
from logger import Log


__author__ = "Alejandro Gonzales-Irribarren"
__email__ = "jose.gonzalesdezavala1@unmsm.edu.pe"
__github__ = "https://github.com/alejandrogzi"
__version__ = "0.8.0-devel"


def query_table(path: str) -> pd.DataFrame:
    """
    Return a pandas DataFrame with all projections and metadata.

    @type path: str
    @param path: path to the results directory
    """

    log = Log.connect(path, Constants.FileNames.LOG)

    # Reads orthology_classification, loss_sum_data, and ortholog_scores.
    orthology = pd.read_csv(os.path.join(path, Constants.FileNames.ORTHOLOGY), sep="\t")
    loss = pd.read_csv(
        os.path.join(path, Constants.FileNames.CLASS),
        sep="\t",
        header=None,
        names=["projection", "transcript", "class"],
    )
    score = pd.read_csv(os.path.join(path, Constants.FileNames.SCORES), sep="\t")
    isoforms = pd.read_csv(
        os.path.join(path, Constants.FileNames.ISOFORMS), sep="\t", header=None
    )
    paralogs = pd.read_csv(os.path.join(path, Constants.FileNames.PARALOGS), sep="\t", header=None, names=["transcripts"])
    # quality = pd.read_csv(os.path.join(path, Constants.FileNames.QUALITY), sep="\t")

    # Creates a dictionary: transcript -> gene
    isoforms_dict = isoforms.set_index(1).to_dict().get(0)

    # Subsets loss to consider only projections
    loss = loss[loss["projection"] == "PROJECTION"]
    loss["helper"] = loss["transcript"].str.rsplit(".", n=1).str[0]

    ortho_x_loss = pd.merge(
        orthology, loss, left_on="q_transcript", right_on="transcript", how="outer"
    )

    ortho_x_loss["helper"].fillna(ortho_x_loss["t_gene"], inplace=True)

    # Merge transcript names (under the column "gene") and chain IDs (under the column "chain")
    score["transcripts"] = [f"{k}.{v}" for k,v in zip(score["gene"], score["chain"])]
    score = score[["transcripts", "pred", "gene"]]

    table = pd.merge(ortho_x_loss, score, left_on="transcript", right_on="transcripts", how="left")

    # Create a new column with a rename orthology relationship
    table["relation"] = table["orthology_class"].map(Constants.ORTHOLOGY_TYPE)
    table["t_gene"].fillna(table["helper"].map(isoforms_dict), inplace=True)

    # Add paralog probabilities -> disabled for now 
    # paralog = pd.merge(score, paralogs, on="transcripts").groupby("gene").agg({"pred": "max"}).reset_index()
    # paralog.columns = ["helper", "paralog_prob"]
    # table = pd.merge(table, paralog, on="helper", how="left")
    # table["paralog_prob"].fillna(0, inplace=True)

    # # Merge quality data
    # table = pd.merge(table, quality, left_on="transcripts", right_on="Projection_ID")

    table = table[
        [
            "t_gene",
            "helper",
            "transcripts",
            "relation",
            "class",
            "pred",
            "q_gene",
            "paralog_prob",
            # "confidence_level",
        ]
    ]

    info = [
        f"found {len(table)} projections, {len(table['helper'].unique())} unique transcripts, {len(table['t_gene'].unique())} unique genes",
        f"class stats: {table['class'].value_counts().to_dict()}",
        f"relation stats: {table['relation'].value_counts().to_dict()}"
        # f"confidence stats: {table['confidence_level'].value_counts().to_dict()}",
    ]

    [log.record(i) for i in info]

    return table
