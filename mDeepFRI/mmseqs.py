import csv
import gzip
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Dict, Iterable, List, Literal

import numpy as np
from pysam import FastaFile, FastxFile, tabix_compress

import mDeepFRI
from mDeepFRI.utils import run_command

ESM_DATABASES = ["highquality_clust30", "esmatlas", "esmatlas_v2023_02"]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(module)s.%(funcName)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)


@dataclass
class ValueRange:
    min: float
    max: float


def _createdb(sequences_file, db_path):
    """
    Converts FASTA file to a DB format needed for MMseqs2.
    This should generate five files,
    e.g. queryDB, queryDB_h and its corresponding index file queryDB.index,
    queryDB_h.index and queryDB.lookup from the FASTA QUERY.fasta input sequences.

    sequence_file (str): path to FASTA file.
    db_path (str): path to output db file.

    Returns:
        None
    """
    run_command(f"mmseqs createdb {sequences_file} {db_path} --dbtype 1")


def _createindex(db_path: str, threads: int = 1):
    with tempfile.TemporaryDirectory() as tmp_path:
        run_command(
            f"mmseqs createindex {db_path} {tmp_path} --threads {threads}")


def create_target_database(fasta_path: str,
                           mmseqs_db_path: str,
                           index: bool = True,
                           threads: int = 1) -> None:
    """
    Extracts sequences from compressed FoldComp database.

    Args:
        fasta_path (str): Path to FoldComp database.
        mmseqs_db_path (str): Path to new MMSeqs database.
        index (bool): Create index for MMSeqs database.
        threads (int): Number of threads to use.


    Returns:
        None
    """
    _createdb(fasta_path, mmseqs_db_path)
    if index:
        _createindex(mmseqs_db_path, threads)


def _search(query_db: str,
            target_db: str,
            result_db: str,
            mmseqs_max_eval: float = 10e-5,
            sensitivity: Annotated[float, ValueRange(min=1.0, max=7.5)] = 5.7,
            threads: int = 1):
    with tempfile.TemporaryDirectory() as tmp_path:
        run_command(
            f"mmseqs search -e {mmseqs_max_eval} --threads {threads} "
            f"-s {sensitivity} {query_db} {target_db} {result_db} {tmp_path}")


def _convertalis(
    query_db: str,
    target_db: str,
    result_db: str,
    output_file: str,
    columns: Literal["query", "target", "fident", "alnlen", "mismatch",
                     "gapopen", "qstart", "qend", "tstart", "tend", "qcov",
                     "tcov", "evalue", "bits", "qseq", "tseq", "qheader",
                     "theader", "qaln", "taln", "qframe", "tframe", "mismatch",
                     "qcov", "tcov", "qset", "qsetid", "tset", "tsetid",
                     "taxid", "taxname", "taxlineage", "qorfstart", "qorfend",
                     "torfstart", "torfend", "ppos"] = [
                         "query", "target", "fident", "alnlen", "mismatch",
                         "gapopen", "qstart", "qend", "tstart", "tend", "qcov",
                         "tcov", "evalue", "bits"
                     ]):

    args = ",".join(columns)
    run_command(
        f"mmseqs convertalis {query_db} {target_db} {result_db} {output_file} --format-mode 4 "
        f"--format-output {args}")


class MMSeqsSearchResult(np.recarray):
    """
    Class for handling MMSeqs2 search results. The results are stored in a TSV file.
    Inherits from numpy.recarray.

    Args:
        data (np.recarray): MMSeqs2 search results.
        query_fasta (str): Path to query FASTA file.
        database (str): Path to MMSeqs2 database.

    Attributes:
        data (np.recarray): MMSeqs2 search results.
        query_fasta (str): Path to query FASTA file.
        database (str): Path to MMSeqs2 database.
        columns (np.array): Array with column names.

    Example:

            >>> from mDeepFRI.mmseqs import MMSeqsSearchResult
            >>> result = MMSeqsSearchResult.from_filepath("path/to/file.tsv")
            >>> # sort file by identity and select seq1 hits only
            >>> result[::-1].sort(order=["fident"])
            >>> seq1_hits = result[result["query"] == "seq1"]
            >>> # save results
            >>> result.save("path/to/file.tsv")
    """
    def __init__(self, data, query_fasta=None, database=None):
        self.data = data
        self.query_fasta = Path(query_fasta).resolve()
        self.database = Path(database).resolve()

    def __new__(cls, data, query_fasta=None, database=None):
        obj = np.asarray(data).view(cls)
        obj.query_fasta = query_fasta
        obj.database = database
        return obj

    @property
    def columns(self):
        return np.array(self.data.dtype.names)

    def save(self, filepath, filetype: Literal["tsv", "npz"] = "tsv"):
        """
        Save search results to TSV or NumPy compressed file. NPZ does not
        preserve information about query file and database.

        Args:
            filepath (str): Path to output file.
            filetype (str): File type to save. Options: "tsv" or "npz".

        Returns:
            None

        Example:

            >>> from mDeepFRI.mmseqs import MMSeqsSearchResult
            >>> result = MMSeqsSearchResult.from_filepath("path/to/file.tsv")
            >>> result.save("path/to/file.tsv")
        """

        if filetype == "tsv":
            with open(filepath, "w", newline="") as f:
                # write comments
                f.write(f"#Query:{self.query_fasta}\n")
                f.write(f"#Database:{self.database}\n")
                # write tsv
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(self.dtype.names)
                for row in self:
                    writer.writerow(row)

        elif filetype == "npz":
            np.savez_compressed(filepath, self.data)

        else:
            raise ValueError("File type should be 'tsv' or 'npz'.")

    @classmethod
    def from_filepath(cls, filepath, query_fasta=None, database=None):
        """
        Load search results from TSV file.

        Args:
            filepath (str): Path to TSV file from convertalis.
            query_fasta (str): Path to query FASTA file (optional).
            database (str): Path to MMSeqs2 database (optional).

        Returns:
            MMSeqsSearchResult: MMSeqs2 search results.

        Example:

                >>> from mDeepFRI.mmseqs import MMSeqsSearchResult
                >>> result = MMSeqsSearchResult.from_filepath("path/to/file.tsv")
        """

        data = np.recfromcsv(filepath,
                             delimiter="\t",
                             encoding="utf-8",
                             names=True)
        return cls(data, query_fasta, database)


class QueryFile:
    """
    Class for handling FASTA files with sequences to query against MMSeqs2 database.

    Args:
        filepath (str): Path to FASTA file.

    Attributes:
        filepath (str): Path to FASTA file.
        sequences (Dict[str, str]): Dictionary with sequence IDs as keys and sequences as values.
        too_long (List[str]): List of sequence IDs that were too long.
        too_short (List[str]): List of sequence IDs that were too short.
    """
    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.sequences: Dict[str, str] = {}
        self.too_long: List[str] = []
        self.too_short: List[str] = []

    def __repr__(self) -> str:
        return f"QueryFile(filepath={self.filepath})"

    def __str__(self) -> str:
        return f"QueryFile(filepath={self.filepath})"

    def __setitem__(self, key, value) -> None:
        self.sequences[key] = value

    def __getitem__(self, key) -> None:
        return self.sequences[key]

    def load_sequences(self) -> None:
        """
        Load sequences from FASTA file. Sequences are stored in a dictionary with sequence
        IDs as keys and sequences as values.

        Note:
            This method should be called only if maniuplating sequences directly is needed.

        Returns:
            None

        Example:

            >>> from mDeepFRI.mmseqs import QueryFile
            >>> query_file = QueryFile("path/to/file.fasta")
            >>> query_file.load_sequences()
        """

        with FastxFile(self.filepath) as f:
            for entry in f:
                self.sequences[entry.name] = entry.sequence

    def load_ids(self, ids: Iterable[str]) -> None:
        """
        Load sequences by ID from FASTA file. The file is indexed with `samtools faidx`
        to speed up the process. Sequences are stored in a dictionary with
        sequence IDs as keys and sequences as values.

        Note:
            This method allows to load only sequences with specified IDs,
            which can be useful when working with large FASTA files.
            `samtools faidx` works with uncompressed FASTA files, and files compressed with bgzip.
            If compression is wrong, the file will be automatically re-compressed.

        Args:
            ids (List[str]): List of sequence IDs to load.

        Returns:
            None

        Raises:
            ValueError: If sequence with specified ID is not found in FASTA file.

        Example:
                >>> from mDeepFRI.mmseqs import QueryFile
                >>> query_file = QueryFile("path/to/file.fasta")
                >>> query_file.load_ids(["seq1", "seq2"])
        """
        # check if exists
        filepath = Path(self.filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File {self.filepath} not found.")

        try:
            fasta = FastaFile(self.filepath)
        # catch gzipped files and recompress with bgzip
        except OSError:
            # unzip file
            with gzip.open(self.filepath, "rt") as f:
                content = f.read()
            # write to new file
            new_filepath = Path(self.filepath).parent / Path(
                self.filepath).stem
            with open(new_filepath, "w") as f:
                f.write(content)
                # index file
                tabix_compress(new_filepath, new_filepath + ".gz", force=True)

        with fasta:
            for seq_id in ids:
                try:
                    self.sequences[seq_id] = fasta.fetch(seq_id)
                except KeyError:
                    raise ValueError(
                        f"Sequence with ID {seq_id} not found in {self.filepath}"
                    )

    def filter_sequences(self, min_length: int = None, max_length: int = None):
        """
        Filter sequences by length.

        Args:
            min_length (int): Minimum sequence length.
            max_length (int): Maximum sequence length.

        Returns:
            None

        Example:

            >>> from mDeepFRI.mmseqs import QueryFile
            >>> query_file = QueryFile("path/to/file.fasta")
            >>> query_file.load_sequences()
            >>> query_file.filter_sequences(min_length=50, max_length=200)
        """
        # check if sequences were loaded
        if not self.sequences:
            raise ValueError(
                "No sequences loaded. Use load_sequences() or load_ids() method to load sequences from FASTA file."
            )

        filtered_sequences = self.sequences.copy()
        if min_length:
            filtered_sequences = {
                k: v
                for k, v in filtered_sequences.items() if len(v) >= min_length
            }
            if not filtered_sequences:
                raise ValueError(
                    "No sequences left after filtering by minimum sequence length."
                )
            self.too_long = list(
                set(self.sequences.keys()) - set(filtered_sequences.keys()))

        if max_length:
            filtered_sequences = {
                k: v
                for k, v in filtered_sequences.items() if len(v) <= max_length
            }
            if not filtered_sequences:
                raise ValueError(
                    "No sequences left after filtering by maximum sequence length."
                )
            self.too_short = list(
                set(self.sequences.keys()) - set(filtered_sequences.keys()))

        self.sequences = filtered_sequences

    def search(self,
               database_path: str,
               eval: float = 10e-5,
               sensitivity: Annotated[float,
                                      ValueRange(min=1.0, max=7.5)] = 5.7,
               index_target: bool = True,
               threads: int = 1):
        """
        Queries sequences against MMSeqs2 database. The search results are stored in a tabular format.

        Args:
            database_path (str): Path to MMSeqs2 database or database FASTA.
            eval (float): Maximum e-value for MMSeqs2 search.
            sensitivity (float): Sensitivity value for MMSeqs2 search.
            index_target (bool): Create index for target database. Advised for repeated searches.
            threads (int): Number of threads to use.

        Returns:
            result (MMSeqsSearchResult): MMSeqs2 search results.

        Example:

                >>> from mDeepFRI.mmseqs import QueryFile
                >>> query_file = QueryFile("path/to/file.fasta")
                >>> query_file.load_sequences()
                >>> query_file.filter_sequences(min_length=50, max_length=200)
                >>> result = query_file.search("path/to/database")
        """
        # check sensitivity values
        if not 1.0 <= sensitivity <= 7.5:
            raise ValueError(
                "Sensitivity value should be between 1.0 and 7.5.")

        with tempfile.TemporaryDirectory() as tmp_path:
            if self.sequences:
                fasta_path = Path(tmp_path) / "filtered_query.fa"
                with open(fasta_path, "w") as f:
                    for seq_id, seq in self.sequences.items():
                        f.write(f">{seq_id}\n{seq}\n")
            else:
                fasta_path = self.filepath

            # create query db
            input_db_path = Path(tmp_path) / "query.mmseqsDB"
            _createdb(fasta_path, input_db_path, index=False)

            # create target db
            with open(database_path, "r") as f:
                first_line = f.readline()

            if first_line.startswith(">"):
                target_db_path = Path(database_path).with_suffix(".mmseqsDB")
                _createdb(database_path, target_db_path, index=index_target)
            else:
                target_db_path = database_path

            result_db = Path(tmp_path) / "search_resultDB"
            _search(input_db_path, target_db_path, result_db, eval,
                    sensitivity, threads)

            output_file = Path(tmp_path) / "search_results.tsv"
            _convertalis(input_db_path, target_db_path, result_db, output_file)

            result = MMSeqsSearchResult.from_filepath(
                output_file,
                query_fasta=fasta_path,
                database=target_db_path,
            )

        return result


def extract_fasta_foldcomp(foldcomp_db: str,
                           output_file: str,
                           threads: int = 1):
    """
    Extracts FASTA from database
    """
    foldcomp_bin = Path(mDeepFRI.__path__[0]).parent / "foldcomp_bin"
    database_name = Path(foldcomp_db).stem

    # run command
    run_command(
        f"{foldcomp_bin} extract --fasta -t {threads} {foldcomp_db} {output_file}"
    )

    if database_name in ESM_DATABASES:
        # use sed to correct the headers
        os.system(
            fr"sed -i 's/^>\(ESMFOLD V0 PREDICTION FOR \)\(.*\)/>\2/' {output_file}"
        )

    # gzip fasta file
    tabix_compress(output_file, str(output_file) + ".gz", force=True)
    # remove unzipped file
    os.remove(output_file)
    # remove possible previous index, might lead to errror
    try:
        os.remove(str(output_file) + ".gz.fai")
        os.remove(str(output_file) + ".gz.gzi")
    except FileNotFoundError:
        pass

    return Path(str(output_file) + ".gz")


def validate_mmseqs_database(database: str):
    """
    Check if MMSeqs2 database is intact.

    Args:
        database (str): Path to MMSeqs2 database.

    Returns:
        is_valid (bool): True if database is intact.

    """

    # Verify all the files for MMSeqs2 database
    mmseqs2_ext = [
        ".index", ".dbtype", "_h", "_h.index", "_h.dbtype", ".idx",
        ".idx.index", ".idx.dbtype", ".lookup", ".source"
    ]

    target_db = Path(database)
    is_valid = True
    for ext in mmseqs2_ext:
        if not os.path.isfile(f"{target_db}{ext}"):
            logger.debug(f"{target_db}{ext} is missing.")
            is_valid = False
            break

    return is_valid


# def run_mmseqs_search(query_file: str,
#                       target_db: str,
#                       output_path: str,
#                       mmseqs_max_evalue: float = 10e-5,
#                       threads: int = 1) -> Path:
#     """Creates a database from query sequences and runs mmseqs2 search against database.

#     Args:
#         query_file (str): Path to query FASTA file.
#         target_db (str): Path to target MMSeqs2 database.
#         output_path (str): Path to output folder.
#         mmseqs_min_evalue (float): Minimum e-value for MMSeqs2 search.
#         threads (int): Number of threads to use.

#     Returns:
#         output_file (pathlib.Path): Path to MMSeqs2 search results.
#     """
#     query_file = Path(query_file)
#     target_db = Path(target_db)
#     output_path = Path(output_path)

#     output_path.mkdir(parents=True, exist_ok=True)
#     output_file = output_path / Path(target_db.stem + ".search_results.tsv")
#     query_db = str(output_path / 'query.mmseqsDB')
#     createdb(query_file, query_db)

#     with tempfile.TemporaryDirectory() as tmp_path:

#         result_db = str(Path(tmp_path) / 'search_resultDB')
#         search(query_db,
#                target_db,
#                result_db,
#                mmseqs_max_evalue,
#                threads=threads)

#         # Convert results to tabular format
#         convertalis(query_db, target_db, result_db, output_file)

#     return output_file

# def filter_mmseqs_results(results_file: str,
#                           min_bit_score: float = None,
#                           min_identity: float = None,
#                           k_best_hits: int = 5,
#                           threads: int = 1) -> np.recarray:
#     """
#     Filters MMSeqs results retrieving only k best hits based on identity
#     above specified thresholds. Allows number of paiwise alignments
#     in the next step of pipeline.

#     Args:
#         results_file (pathlib.Path): Path to MMSeqs2 search results.
#         min_bit_score (float): Minimum bit score.
#         min_identity (float): Minimum identity.
#         k_best_hits (int): Number of best hits to keep.
#         threads (int): Number of threads to use.

#     Returns:
#         output (numpy.recarray): Filtered results.
#     """
#     def select_top_k(query, db, k=30):
#         return db[db["query"] == query][:k]

#     output = np.recfromcsv(results_file,
#                            delimiter="\t",
#                            encoding="utf-8",
#                            names=MMSEQS_COLUMN_NAMES)

#     # check if output is not empty
#     if output.size == 0:
#         final_database = None

#     else:
#         # MMSeqs2 alginment filters
#         if min_identity:
#             output = output[output['identity'] >= min_identity]
#         if min_bit_score:
#             output = output[output['bit_score'] >= min_bit_score]

#         # Get k best hits
#         output.sort(order=["query", "identity", "e_value"], kind="quicksort")
#         top_k_db = partial(select_top_k, db=output[::-1], k=k_best_hits)
#         with ThreadPool(threads) as pool:
#             top_k_chunks = pool.map(top_k_db, np.unique(output["query"]))

#         final_database = np.concatenate(top_k_chunks)

#         ## TODO: move logging module a level up
#         logger.info("%i pairs after filtering with k=%i best hits.",
#                     final_database.shape[0], k_best_hits)

#     return final_database
