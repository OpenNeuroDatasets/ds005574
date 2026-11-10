"""
Set the missing physical units for sub-01.

The source EDF for sub-01 has an empty physical dimension field for every
channel, unlike all other subjects, which use "uV" for ECoG and ECG channels.
The stored values are already in microvolts, so only the label is missing.
Loaders like MNE treat a blank unit as volts, which makes sub-01 appear ~1e6
times larger than the other subjects.

This script patches, in place:
1. the 8-byte physical dimension field of the EDF header for ECOG/ECG channels
2. the `units` column of the BIDS channels.tsv for the same channels

Only header bytes are touched; signal data is not modified. The script is
idempotent and can be re-run safely.

The EDF is a locked git-annex file, so unlock it first:
    git annex unlock sub-01/ieeg/sub-01_task-podcast_ieeg.edf
    python code/fix_sub01_units.py --dry-run
    python code/fix_sub01_units.py

References
- https://www.edfplus.info/specs/edf.html
"""

import argparse
from os import path

ROOT = path.dirname(path.dirname(path.abspath(__file__)))
EDF_PATH = path.join(ROOT, "sub-01", "ieeg", "sub-01_task-podcast_ieeg.edf")
TSV_PATH = path.join(ROOT, "sub-01", "ieeg", "sub-01_task-podcast_channels.tsv")

UNIT = "uV"
CH_TYPES = {"ECOG", "ECG"}

# EDF header layout: 256 fixed bytes, then per-channel fields stored as
# contiguous arrays (all labels, then all transducers, then all dims, ...)
LABEL_WIDTH = 16
TRANSDUCER_WIDTH = 80
DIM_WIDTH = 8


def read_tsv(filename: str):
    with open(filename, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    header = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:] if line]
    return header, rows


def write_tsv(filename: str, header: list, rows: list):
    # keep the BOM that the original file has
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


def patch_edf(filename: str, channels: set, dry_run: bool):
    with open(filename, "rb" if dry_run else "r+b") as f:
        fixed = f.read(256)
        n_chans = int(fixed[252:256])
        labels_bytes = f.read(LABEL_WIDTH * n_chans)
        labels = [
            labels_bytes[i * LABEL_WIDTH : (i + 1) * LABEL_WIDTH].decode("ascii").strip()
            for i in range(n_chans)
        ]

        missing = channels - set(labels)
        assert not missing, f"Channels not found in EDF: {missing}"

        dims_offset = 256 + (LABEL_WIDTH + TRANSDUCER_WIDTH) * n_chans
        f.seek(dims_offset)
        dims_bytes = f.read(DIM_WIDTH * n_chans)
        dims = [
            dims_bytes[i * DIM_WIDTH : (i + 1) * DIM_WIDTH].decode("ascii").strip()
            for i in range(n_chans)
        ]

        n_changed = 0
        for i, (label, dim) in enumerate(zip(labels, dims)):
            if label not in channels or dim == UNIT:
                continue
            assert dim == "", f"{label} has unexpected unit {dim!r}"
            n_changed += 1
            if not dry_run:
                f.seek(dims_offset + i * DIM_WIDTH)
                f.write(UNIT.ljust(DIM_WIDTH).encode("ascii"))

    print(f"EDF: {n_changed}/{n_chans} channel units set to {UNIT!r}")


def patch_tsv(filename: str, dry_run: bool) -> set:
    header, rows = read_tsv(filename)
    i_name, i_type, i_units = (header.index(c) for c in ("name", "type", "units"))

    channels = set()
    n_changed = 0
    for row in rows:
        if row[i_type] not in CH_TYPES:
            continue
        channels.add(row[i_name])
        if row[i_units] != UNIT:
            row[i_units] = UNIT
            n_changed += 1

    if not dry_run:
        write_tsv(filename, header, rows)
    print(f"TSV: {n_changed}/{len(rows)} channel units set to {UNIT!r}")

    return channels


def main(args):
    if args.dry_run:
        print("Dry run: no files will be modified")
    elif path.islink(EDF_PATH):
        raise RuntimeError(
            f"{EDF_PATH} is a locked git-annex symlink. "
            "Run `git annex unlock` on it first."
        )
    channels = patch_tsv(TSV_PATH, args.dry_run)
    patch_edf(EDF_PATH, channels, args.dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    main(parser.parse_args())
