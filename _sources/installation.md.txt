# Installation

## 1. Install environment and DeepFRI

1. Clone repo locally
```{code-block} bash
git clone https://github.com/bioinf-mcb/Metagenomic-DeepFRI --recursive
cd Metagenomic-DeepFRI
```
2. Setup conda environment
```{code-block} bash
conda env create --name deepfri --file environment.yml
conda activate deepfri
```
3. Install `meta-DeepFRI`
```{code-block} bash
pip install .
```
4. Verify installation
```{code-block} bash
pytest
deepfri --help
```

## 2. Retrieve `DeepFRI` model weights
### CPU weights
```bash
wget https://users.flatironinstitute.org/~renfrew/DeepFRI_data/newest_trained_models.tar.gz
tar -xf newest_trained_models.tar.gz
```

### GPU weights
```bash
wget https://users.flatironinstitute.org/~renfrew/DeepFRI_data/trained_models.tar.gz
tar -xf trained_models.tar.gz
```

**Attention:** Using DeepFRI with GPU requires extra installation steps, described in section 4. GPU Setup of [tensorfow installation guide](https://www.tensorflow.org/install/pip).
