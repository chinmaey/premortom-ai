# Synthetic Quote Inputs

This folder contains the source files for generating the planned experiment inputs.

The experiment target is:

- 100 bidding processes.
- 20 vendor quotes per bidding process.
- 2,000 total quote inputs.
- 2,000 generated PDF quote files.
- Metadata and ground truth labels for top-1 and top-2 evaluation.

## Files

- `criteria.json`: experiment criteria, weights, guardrails, vendor types, bid categories, and sample-generation settings.
- `synthesize_samples.py`: generates synthetic vendor quote PDFs and metadata from `criteria.json`.

## Generated Output

By default, the script writes generated files to:

```text
files/input/samples/
```

Expected generated structure:

```text
samples/
├── metadata.json
├── coverage.csv
├── bids/
│   ├── BID-001/
│   │   ├── BID-001-Q01.pdf
│   │   └── ...
│   └── ...
└── manifest.csv
```

`metadata.json` contains bid-level context, quote metadata, criteria scores, ground truth labels, and PDF paths. The PDF files are the primary inputs intended for the document extraction pipeline.

Each generated quote includes vendor/company details such as legal company name, address, contact person, years in operation, similar hospital references, and estimated quote length.

`coverage.csv` summarizes coverage across important input dimensions, including equipment type, hospital type, vendor type, quote archetype, quote format, quote length, warranty start, installation responsibility, compliance completeness, and score buckets for each criterion.

For hosted experiments, copy the generated PDF folder to a shared web server and set `pdf_base_url` in `criteria.json`. The generated metadata will then include stable PDF URLs.

## Run

From the repository root:

```bash
python3 files/input/synthesize_samples.py
```

Or with custom paths:

```bash
python3 files/input/synthesize_samples.py \
  --criteria files/input/criteria.json \
  --output files/input/samples
```

Generate a smaller hackathon slice:

```bash
python3 files/input/synthesize_samples.py --num-samples 100
```

Generate samples while preferring dimensions that are under-covered in the existing `samples/metadata.json`:

```bash
python3 files/input/synthesize_samples.py --num-samples 200 --fill-coverage
```

With `--fill-coverage`, the script reads existing `samples/metadata.json`, appends new bids after the latest bid id, and biases new samples toward lower-covered values in `coverage.csv`.

You can also control bid shape directly:

```bash
python3 files/input/synthesize_samples.py --num-bids 10 --quotes-per-bid 10
```

The script requires `reportlab` to create PDF files. It is already listed in the backend requirements.
