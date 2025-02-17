# The "Podcast" ECoG dataset for modeling neural activity during natural story listening

To reproduce constructing this dataset, the following commands should be run in the following order:

1. `make bidsify`: convert raw data from `sourcedata/` into a BIDS dataset.
2. `make ecogqc`: generate quality check reports in `derivatives/ecogqc`.
3. `make mark_bad_channels`: based on the QC reports, this target will mark bad channels in `_channels.tsv` files.
4. `make ecogprep`: run the raw data through the preprocessing pipeline.
5. `make generate_features`: create various stimulus features based on `stimuli/podcast.wav` and `stimuli/podcast_transcript.csv`.
