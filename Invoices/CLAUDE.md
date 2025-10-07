# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demonstration project for **LandingAI's Agentic Document Extraction (ADE)**, focused on extracting structured data from utility bills and invoices. The project uses the `agentic_doc` Python package to parse PDFs and images, applying custom schemas to extract specific fields.

## Environment Setup

The project uses a Python virtual environment located at `venv/`.

**Activate the virtual environment:**
```bash
source venv/bin/activate
```

**Key dependencies:**
- `landingai_ade` - LandingAI's ADE client
- `agentic_doc` - Document parsing library
- `pydantic` and `pydantic-settings` - Schema definition and validation
- `ipykernel` - Jupyter notebook support
- `python-dotenv` - Environment variable management from `.env` file
- `pandas` - Data processing for extracted results
- `tqdm` - Progress bars

## API Key Management

The API key is stored in `.env` as `VISION_AGENT_API_KEY`. Two helper functions are available in `utilities.py`:

- `get_api_key()`: Reads from `os.environ.get("VISION_AGENT_API_KEY")`
- `get_api_key_env()`: Uses `pydantic_settings.BaseSettings` to load from `.env`

**In Jupyter notebooks**, you must load the `.env` file before using the API:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Project Structure

### Core Files

- **`invoices_demo_ade.ipynb`**: Main demonstration notebook showing end-to-end utility bill extraction workflow using a JSON-based schema
- **`invoice_schema.py`**: Pydantic-based extraction schema for invoices, defines `InvoiceExtractionSchema` with nested models for document info, customer info, supplier info, terms/shipping, totals, and line items
- **`utilities.py`**: Helper functions for API key retrieval and saving parse results to JSON

### Data Folders

- **`input_folder/`** and **`input_folder2/`**: Source documents (PDFs, PNGs, JPEGs) for processing
- **`results_folder/`**: JSON output from ADE parse operations, one file per processed document
- **`groundings_folder/`**: Visual grounding data (chunk references) showing where extracted values were found in the source documents
- **`ade_results/`**: Alternative output directory used by `utilities.save_parse_results()`
- **`schema_folder/`**: Storage for schema definitions
- **`images/`**: Images used in notebook markdown cells for documentation

## Working with Jupyter Notebooks

The project uses Jupyter notebooks for demonstrations. The registered kernel is:
- **Kernel name**: `invoices-venv`
- **Display name**: "Python (Invoices venv)"
- **Python path**: `/Users/andreakropp/Documents/Github/andrea-kropp/ade_demos/Invoices/venv/bin/python`

**To register the kernel** (if needed):
```bash
source venv/bin/activate
pip install ipykernel
python -m ipykernel install --user --name=invoices-venv --display-name="Python (Invoices venv)"
```

## Schema Architecture

ADE supports **two schema approaches**:

1. **JSON Schema** (used in `invoices_demo_ade.ipynb`): Define extraction schema as a dictionary with nested objects
2. **Pydantic Models** (defined in `invoice_schema.py`): Type-safe schemas with validation

**Key constraint**: ADE supports **one level of nested schemas only**. The `InvoiceExtractionSchema` demonstrates this with top-level fields containing nested models like `DocumentInfo`, `CustomerInfo`, etc.

## Typical Workflow

1. Place documents (PDFs/images) in `input_folder/`
2. Define or select extraction schema (JSON dict or Pydantic model)
3. Call `parse()` from `agentic_doc` with:
   - `documents`: List of file paths
   - `extraction_schema`: Schema for field extraction
   - `result_save_dir`: Where to save JSON results
   - `grounding_save_dir`: Where to save visual grounding data
4. Process results from JSON files in `results_folder/`
5. Optionally aggregate results into pandas DataFrame for analysis

## Parse Results Structure

Each JSON result contains:
- `markdown`: Markdown summary of extracted data
- `chunks`: List of parsed text/image regions from the document
- `extraction`: Nested dictionary of extracted field values
- `extraction_metadata`: Metadata for each field (chunk references, confidence scores)
- `metadata`: Document-level info (filename, page count, processing time)

## Important Notes

- **Supported formats**: `.pdf`, `.png`, `.jpg`, `.jpeg`
- The `.env` file contains configuration for batch processing (`BATCH_SIZE`, `MAX_WORKERS`, `MAX_RETRIES`, etc.)
- When importing functions from `utilities.py`, use: `from utilities import function_name`
- Visual grounding chunks reference specific regions in source documents where extracted values were found
