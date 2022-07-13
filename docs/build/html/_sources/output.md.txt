# Output

Output folder `FINISHED_PATH / project_name / timestamp` will contain:

1. `query_files/*` - directory containing all input query files.
2. `mmseqs2_search_results.m8`
3. `alignments.json` - results of alignment search implemented in `utils.search_alignments.py`
4. `metadata*` - files containing useful information.
5. `results*` - multiple DeepFRI outputs. Organized by model type `['GCN', 'CNN']` and its mode `['mf', 'bp', 'cc', 'ec']` - 8 files in total.
```
mf = molecular_function
bp = biological_process
cc = cellular_component
ec = enzyme_commission
```

Missing results from one model mean that all query protein sequences were aligned correctly or none of them were aligned.
