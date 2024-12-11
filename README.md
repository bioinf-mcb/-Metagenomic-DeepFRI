# 🍳 Metagenomic-DeepFRI [![Stars](https://img.shields.io/github/stars/bioinf-MCB/Metagenomic-DeepFRI.svg?style=social&maxAge=3600&label=Star)](https://github.com/bioinf-MCB/Metagenomic-DeepFRI/stargazers)
[![Support Ukraine](https://img.shields.io/badge/Support-Ukraine-FFD500?style=flat&labelColor=005BBB)](https://u24.gov.ua/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg?style=flat-square&maxAge=2678400)](https://choosealicense.com/licenses/gpl-3.0/)
[![PyPI](https://img.shields.io/pypi/v/mdeepfri.svg?style=flat-square&maxAge=3600&logo=PyPI)](https://pypi.org/project/mdeepfri)
[![Wheel](https://img.shields.io/pypi/wheel/mdeepfri.svg?style=flat-square&maxAge=3600)](https://pypi.org/project/mdeepfri/#files)
[![Python Versions](https://img.shields.io/pypi/pyversions/mdeepfri.svg?style=flat-square&maxAge=600&logo=python)](https://pypi.org/project/mdeepfri/#files)
[![Python Implementations](https://img.shields.io/pypi/implementation/mdeepfri.svg?style=flat-square&maxAge=600&label=impl)](https://pypi.org/project/mdeepfri/#files)
[![Source](https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=2678400&style=flat-square)](https://github.com/bioinf-MCB/Metagenomic-DeepFRI/)
[![GitHub issues](https://img.shields.io/github/issues/bioinf-MCB/Metagenomic-DeepFRI.svg?style=flat-square&maxAge=600)](https://github.com/bioinf-MCB/Metagenomic-DeepFRI//issues)
[![Docs](https://img.shields.io/readthedocs/metagenomic-deepfri/latest?style=flat-square&maxAge=600)](https://metagenomic-deepfri.readthedocs.io/)
[![Changelog](https://img.shields.io/badge/keep%20a-changelog-8A0707.svg?maxAge=2678400&style=flat-square)](https://github.com/bioinf-MCB/Metagenomic-DeepFRI/blob/main/CHANGELOG.md)
[![Downloads](https://img.shields.io/pypi/dm/mdeepfri?style=flat-square&color=303f9f&maxAge=86400&label=downloads)](https://pepy.tech/project/mdeepfri)

*A pipeline for annotation of genes with [DeepFRI](https://github.com/flatironinstitute/DeepFRI), a deep learning model for functional protein annotation with [Gene Ontology (GO) terms](https://geneontology.org/docs/go-annotations/). It incorporates [FoldComp](https://github.com/steineggerlab/foldcomp) databases of predicted protein structures for fast annotation of metagenomic gene catalogues.*

## Python requirements
Python >= 3.9; < 3.12
The app was tested for 3.11.

## 🔍 Overview
Proteins perform most of the work of living cells. Amino acid sequence and structural features of proteins determine a wide range of functions: from binding specificity and conferring mechanical stability, to catalysis of biochemical reactions, transport, and signal transduction.
DeepFRI is a neural network designed to predict protein function within the framework of the Gene Ontology (GO). The exponential growth in the number of available protein sequences, driven by advancements in low-cost sequencing technologies and computational methods (e.g. gene prediction), has resulted in a pressing need for efficient software to facilitate the annotation of protein databases.
Metagenomic-DeepFRI addresses such needs, building upon efficient libraries. It incorporates novel databases of predicted structures (AlphaFold, ESMFold, MIP, etc.) and improves runtimes of DeepFRI by [2-12 times](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/blob/main/weight_convert/onnx_vs_tf2.png)!

### 📋 Pipeline stages

1. Search proteins similar to query in PDB and supply `FoldComp` databases with `MMSeqs2`.
2. Find the best alignment among `MMSeqs2` hits using `PyOpal`.
3. Align target protein contact map to query protein with unknown structure.
4. Run `DeepFRI` with the structure if found in the database, otherwise run `DeepFRI` with sequence only.

![image.png](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/blob/main/docs/_images/mdeepfri-design.drawio.png)

### 🛠️ Built With

* [MMseqs2](https://github.com/soedinglab/MMseqs2)
* [pyOpal](https://github.com/althonos/pyOpal)
* [DeepFRI](https://github.com/flatironinstitute/DeepFRI)
* [FoldComp](https://github.com/steineggerlab/foldcomp)
* [ONNX](https://github.com/onnx/onnx)

## 🔧 Installation

1. Install from PyPI. Installation might take a few minutes due to download of MMseqs2 binaries.
```{code-block} bash
pip install mdeepfri
```
2. Run and view the help message.
```{code-block} bash
mDeepFRI --help
```

## 💡 Usage
### 1. Prepare structural database
#### 1.1 Existing `FoldComp` databases
The PDB database will be automatically downloaded and installed during the first run of `mDeepFRI`. The PDB suffers from formatting inconsistencies, therefore during PDB alignment around 10% will fail and will be reported via `WARNING`. We suggest coupling PDB search with predicted databases, as it massively improves the structural coverage of the protein universe. A good protein structure allows DeepFRI to annotate the function in more detail. However, the sequence branch of the model has the largest weight, thus even if the predicted structure is erroneous, it will have a minor effect on the prediction. The details can be found in [the original manuscript, fig. 2A](https://www.nature.com/articles/s41467-021-23303-9/figures/2).

You can download additional databases from [website](https://foldcomp.steineggerlab.workers.dev/). During a first run, FASTA sequences will be extracted from `FoldComp` database and `MMseqs2` database will be created and indexed. You can use different databases, but be mindful that computation time might increase exponentially with the size of the database.

Tested databases:
- `afdb_swissprot`
- `afdb_swissprot_v4`
- `afdb_rep_v4`
- `afdb_rep_dark_v4`
- `afdb_uniprot_v4`
- `esmatlas`
- `esmatlas_v2023_02`
- `highquality_clust30`


`ATTENTION:` Please, do not rename downloaded databases. `FoldComp` has certain inconsistencies in the way FASTA sequences are extracted ([example](https://github.com/steineggerlab/foldcomp/issues/51)), therefore pipeline was tweaked for each database. If database you need does not work, please report in [issues](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/issues) and we will add it as soon as possible. Sorry for the inconvenience.

`ATTENTION:` database creation is a very sensitive step which relies on external software. If pipeline is interrupted during this step, the databases might be corrupted. If you are not sure about your database, rerun the pipeline with `--overwrite` flag - it will rerun database creation process.

#### 1.2. Custom `FoldComp` database
In order to use personal database of structures, you will have to create a custom FoldComp database. For that, download a `FoldComp` executable and run  the following command:
```
foldcomp compress [-t number] <dir|tar(.gz)> [<dir|tar|db>]
```

### 2. Download models
Two versions of models available:
- `v1.0` - is the original version from DeepFRI publication.
- `v1.1` - is a version finetuned on AlphaFold models and machine-generated Gene Ontology Uniprot annotations. You can read details about `v1.1` in [ISMB 2023 presentation by Pawel Szczerbiak](https://docs.google.com/presentation/d/1Pzn_gQH5-dDImpApSoWFQNu3WByFZYWqfesplANK9hI/edit?usp=sharing)

To download models run command:
```
mDeepFRI get-models --output path/to/weights/folder -v {1.0 or 1.1}
```

### 3. Predict protein function & capture log
```
mDeepFRI predict-function -i /path/to/protein/sequences -d /path/to/foldcomp/database/ -w /path/to/deepfri/weights/folder -o /output_path 2> log.txt
```

The `logging` module writes output into `stderr`, so use `2>` to redirect it to the file.
Other available parameters can be found upon command `mDeepFRI --help`.

## ✅ Results
The output folder will contain:
1. `{database_name}.search_results.tsv`
2. `query.mmseqsDB` + index from MMSeqs2 search.
3. `results.tsv` - a final output from the DeepFRI model.

### Example output (`results.tsv`)
|  Protein     | GO_term/EC_numer | Score | Annotation                                   | Neural_net | DeepFRI_mode | DB_hit        | DB_name        |Identity |
|--------------|------------------|-------|----------------------------------------------|------------|--------------|---------------|----------------|------------|
| MIP_00215364 | GO:0016798       | 0.218 | hydrolase activity, acting on glycosyl bonds | gcn        | mf           | MIP_00215364  | mip_rosetta_hq |0.933      |
| 1GVH_1 | GO:0009055       | 0.217 | electron transfer activity	                 | gnn        | mf           | 	AF-P24232-F1-model_v4 | afdb_swissprot_v4 | 1.0  |
| unaligned | 3.2.1.-          | 0.215 | 3.2.1.-                        | cnn        | ec           | nan | nan | nan

This is an example of protein annotation with the AlphaFold database.
- Protein - the name of the protein from the FASTA file.
- GO_term/EC_numer - predicted GO term or EC number (dependent on mode)
- Score - DeepFRI score, translates to model confidence in prediction. Details in [publication](https://www.nature.com/articles/s41467-021-23303-9).
- Annotation - annotation from ontology
- Neural_net - type of neural network used for prediction (gcn = Graph Convolutional Network; cnn = Convolutional Neural Network). GCN (Graph Convolutional Network) is used when structural information is available in the database, allowing for generally more confident predictions. When there are no proteins above similarity cut-off (50% identity by default), CNN is used.
- DeepFRI_mode:
   ```
   mf = molecular_function
   bp = biological_process
   cc = cellular_component
   ec = enzyme_commission
   ```
- DB_hit - name of the hit in the database. Empty if no hit was found.
- DB_name - name of the database. Empty if no hit was found.
- Identity - sequence identity between query and hit. Empty if no hit was found.

## ⚙️Features
### 1. Prediction modes
The GO ontology contains three subontologies, defined by their root nodes:
- Molecular Function (MF)
- Biological Process (BP)
- Cellular Component (CC)
- Additionally, Metagenomic-DeepFRI v1.0 is able to predict Enzyme Comission number (EC).
By default, the tool makes predictions in all 4 categories. To select only a few pass the parameter `-p` or `--processing-modes` few times, i.e.:
```
mDeepFRI predict-function -i /path/to/protein/sequences -d /path/to/foldcomp/database/ -w /path/to/deepfri/weights/folder -o /output_path -p mf -p bp
```

### 2. Hierarchical database search
Different databases have a different level of evidence. For example, PDB structures are real experimental structures, thus they are considered to be the data of highest quality. Therefore new proteins are first queried against PDB. Computational predictions differ by quality, i.e. AlphaFold predictions are often more accurate than ESMFold predictions. We provide an opporunity to search multiple databases in a hierarchical manner. For example, if you want to search AlphaFold database first, and then ESMFold, you can pass the parameter `-d` or `--databases` few times, i.e.:
```
mDeepFRI predict-function -i /path/to/protein/sequences -d /path/to/alphafold/database/ -d /path/to/another/esmcomp/database/ -w /path/to/deepfri/weights/folder -o /output_path
```

### 3. Temporary files
The first run of `mDeepFRI` with the database will create temporary files, needed for the pipeline. If you don't want to keep them for the next run add
flag `--remove-intermediate`.

### 4. CPU / GPU utilization
If argument `threads` is provided, the app will parallelize certain steps (alignment, contact map alignment, functional annotation).
GPU is often used to speed up neural networks. Metagenomic-DeepFRI takes care of this and, if CUDA is installed on your machine, `mDeepFRI` will automatically use it for prediction. If not, the model will use CPUs.
**Technical tip:** Single instance of DeepFRI on GPU requires 2GB VRAM. Every currently available GPU with CUDA support should be able to run the model.

## 🔖 Citations
Metagenomic-DeepFRI is a scientific software. If you use it in an academic work, please cite the papers behind it:
- Gligorijević et al. "Structure-based protein function prediction using graph convolutional networks" Nat. Comms. (2021). https://doi.org/10.1038/s41467-021-23303-9
- Steinegger & Söding "MMseqs2 enables sensitive protein sequence searching for the analysis of massive data sets" Nat. Biotechnol. (2017) https://doi.org/10.1038/nbt.3988
- Kim, Midrita & Steinegger "Foldcomp: a library and format for compressing and indexing large protein structure sets" Bioinformatics (2023) https://doi.org/10.1093/bioinformatics/btad153
- Maranga et al. "Comprehensive Functional Annotation of Metagenomes and Microbial Genomes Using a Deep Learning-Based Method" mSystems (2023) https://doi.org/10.1128/msystems.01178-22

## 💭 Feedback

### ⚠️ Issue Tracker

Found a bug ? Have an enhancement request ? Head over to the [GitHub issue
tracker](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/issues) if you need to report
or ask something. If you are filing in on a bug, please include as much
information as you can about the issue, and try to recreate the same bug
in a simple, easily reproducible situation.

### 🏗️ Contributing

Contributions are more than welcome! See
[`CONTRIBUTING.md`](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/blob/main/CONTRIBUTING.md)
for more details.

## 📋 Changelog

This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html)
and provides a [changelog](https://github.com/bioinf-mcb/Metagenomic-DeepFRI/blob/main/CONTRIBUTING.md)
in the [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) format.


## ⚖️ License

This library is provided under the [The 3-Clause BSD License](https://opensource.org/license/bsd-3-clause/).
