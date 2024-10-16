# Monkey in the middle ECoG dataset

data `/scratch/gpfs/zzada/ecog-narratives/monkey`

To reproduce constructing this dataset, the following commands should be run in the following order:

1. `make bidsify`: convert raw data from `sourcedata/` into a BIDS dataset.
2. `make ecog_qc`: generate quality check reports in `derivatives/ecogqc`.
3. `make mark_bad_channels`: based on the QC reports, this target will mark bad channels in `_channels.tsv` files.
4. `make preprocess`: run the raw data through the preprocessing pipeline.
5. `make generate_features`: create various stimulus features based on `stimuli/monkey.wav` and `stimuli/monkey_transcript.csv`.
