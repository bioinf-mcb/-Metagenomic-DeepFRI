## Results

Finished folder will contain:
1. `query_files/*` - directory containing all input query files.
2. `mmseqs2_search_results.m8` - MMseqs2 search results.
3. `alignments.json` - results of alignment search implemented in `utils.search_alignments.py`
4. `metadata*` - files with some useful info.
5. `results*` - multiple files from DeepFRI. Organized by model type ['GCN' / 'CNN'] and its mode ['mf', 'bp', 'cc', 'ec'] for the total of 8 files.
Sometimes results from one model can be missing which means that all query proteins sequences were aligned correctly or none of them were aligned.
   ```
   mf = molecular_function
   bp = biological_process
   cc = cellular_component
   ec = enzyme_commission
   ```
