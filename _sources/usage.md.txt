# Usage

## 1. Prepare database

1. Upload structure (`.pdb` or `.mmcif`, can be gzipped) files to a folder in your system.
2. Run command:
   ```
   deepfri_db_build --input path/to/folder/with/strucures --output path/to/database
   ```
**Tip:** building a database from AF20Swissprot (~550k predicted structures) on 32 CPU cores took ~30 min.

Use parameter `-max_len` to define maximal length of the protein. Due to initial DeepFRI training set default value is set to `1000`.

Main feature of this project is its ability to generate query contact map on the fly
using results from mmseqs2 target database search for similar protein sequences with known structures.
Later in the `metagenomic_deepfri.py` contact map alignment is performed to use it as input to DeepFRI GCN.
(implemented in CPP_lib/load_contact_maps.h)

The command will search for structure files,
process them and store protein sequence and atoms positions inside `database/seq_atom_db`.
It will also create a mmseqs2 database within `database/`.

You can also use `--input DIR_1 FILE_2 ...` argument list to parse structures from multiple sources.

Protein ID is used as a filename. A new protein whose ID already exists in the database will be skipped.
Use `--overwrite` flag to overwrite existing sequences and atoms positions.

## 2. Predict protein function
   ```
   deepfri -i /path/to/protein/sequences -db /path/to/database/folder/from/previous/step -w /path/to/deepfri/weights/folder -o /output_path
   ```
**Attention:** Single instance of DeepFRI on GPU requires 10GB VRAM.
Other available parameters can be found upon command `deepfri --help`.

# Available parameters

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Parameter
     - Description
     - Default value
   * - `--processing_modes`
     - DeepFRI prediction mode.
         mf = molecular_function
         bp = biological_process
         cc = cellular_component
         ec = enzyme_commission
     - `mf,bp,cc,ec`
   * - `--angstrom_contact_thresh`
     - Angstrom contact threshold.
     - 6
   * - `--generate_contacts`
     - Gap fill during contact map alignment.
     - 2
   * - `--mmseqs_min_bit_score`
     - Minimum bit score for MMSeqs2 search.
     - None
   * - `--mmseqs_max_evalue`
     - Maximum e-value for MMSeqs2 search.
     - None
   * - `--mmseqs_min_identity`
     - Minimum sequence identity for MMSeqs2 search.
     - 0.5
   * - `--mmseqs_min_bit_score`
     - Minimum bit score for MMSeqs2 search.
     - None
   * - `--threads`
     - Number of threads to use for parallel processing.
     - 1
