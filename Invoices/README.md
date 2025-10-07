# Invoice Processing with LandingAI ADE

A demonstration project showcasing **LandingAI's Agentic Document Extraction (ADE)** for automated invoice and document processing. This project extracts structured data from PDFs and images using AI-powered parsing and custom extraction schemas.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Functions](#api-functions)
- [Data Pipeline](#data-pipeline)
- [Snowflake Integration](#snowflake-integration)
- [Configuration](#configuration)

## 🎯 Overview

This project demonstrates a complete document processing pipeline using LandingAI's Agentic Document Extraction (ADE) service. It provides:

- **Automated parsing** of invoices from PDFs and images
- **Structured extraction** using Pydantic schemas
- **Parallel processing** for batch operations
- **Database-ready output** with Snowflake-compatible schemas
- **Interactive notebook** for exploration and testing

## ✨ Features

- 🔄 **Parse & Extract**: Two-stage pipeline for document understanding and data extraction
- 🚀 **Parallel Processing**: Process multiple documents concurrently with progress tracking
- 📊 **Pandas Integration**: Convert results to structured DataFrames for analysis
- 🗄️ **Snowflake Ready**: Output tables match production database schema
- 🎨 **Visual Grounding**: Track where extracted values were found in source documents
- 🔧 **Flexible Schemas**: Support for both JSON and Pydantic-based extraction schemas

## 📦 Prerequisites

- Python 3.8+
- LandingAI API key (obtain from [va.landing.ai](https://va.landing.ai/settings/api-key))
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone and Navigate

```bash
cd Invoices
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install landingai_ade pydantic pydantic-settings python-dotenv pandas tqdm ipykernel
```

### 4. Register Jupyter Kernel

```bash
python -m ipykernel install --user --name=invoices-venv --display-name="Python (Invoices venv)"
```

### 5. Configure API Key

Create a `.env` file in the project root:

```bash
VISION_AGENT_API_KEY=your_api_key_here
BATCH_SIZE=50
MAX_WORKERS=2
MAX_RETRIES=5
MAX_RETRY_WAIT_TIME=30
RETRY_LOGGING_STYLE=log_msg
```

## 🎬 Quick Start

### Using the Jupyter Notebook

1. Open `invoices_demo_ade.ipynb`
2. Select the "Python (Invoices venv)" kernel
3. Run cells sequentially to see the complete workflow

### Using Python Scripts

#### Single Document Processing

```python
from landingai_ade import LandingAIADE
from utilities import parse_extract_save
from invoice_schema import InvoiceExtractionSchema
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client
client = LandingAIADE(apikey=os.environ.get("VISION_AGENT_API_KEY"))

# Process single invoice
parse_result, extract_result = parse_extract_save(
    "input_folder/invoice.pdf",
    client,
    InvoiceExtractionSchema,
    output_dir="./results_folder"
)

print(f"Invoice Number: {extract_result.extraction['invoice_info']['invoice_number']}")
print(f"Total: {extract_result.extraction['totals_summary']['total_due']}")
```

#### Batch Processing with Parallel Execution

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Setup
input_dir = Path("input_folder")
output_dir = Path("results_folder")
file_paths = [p for p in input_dir.glob("*.*") if p.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg")]

# Worker function
def process_file(path):
    try:
        return parse_extract_save(path, client, InvoiceExtractionSchema, output_dir=output_dir)
    except Exception as e:
        print(f"❌ {path.name} failed: {e}")
        return None

# Parallel execution
results_summary = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_file, p) for p in file_paths]
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
        result = future.result()
        if result:
            results_summary.append(result)

print(f"✅ Completed {len(results_summary)}/{len(file_paths)} documents")
```

#### Create Summary Tables

```python
from utilities import create_invoice_summary_tables

# Single document mode
invoice_summaries = create_invoice_summary_tables(parse_result, extract_result)

# OR batch mode (from parallel processing)
invoice_summaries = create_invoice_summary_tables(results_summary)

# Access the 4 DataFrames
markdown_df = invoice_summaries[0]      # Full markdown per document
chunks_df = invoice_summaries[1]        # Parsed chunks with grounding
invoices_main_df = invoice_summaries[2] # Invoice-level fields
line_items_df = invoice_summaries[3]    # Line items detail

# Display summary
print(f"Processed {len(invoices_main_df)} invoices")
print(f"Total chunks: {len(chunks_df)}")
print(f"Total line items: {len(line_items_df)}")
```

## 📁 Project Structure

```
Invoices/
├── README.md                    # This file
├── CLAUDE.md                    # AI assistant guidance
├── .env                         # Environment variables (API keys, config)
├── invoice_schema.py            # Pydantic extraction schema
├── utilities.py                 # Helper functions
├── parse-extract.py             # Standalone example script
├── invoices_demo_ade.ipynb      # Interactive demonstration notebook
├── snowflake_setup.sql          # Database schema definitions
│
├── input_folder/                # Source documents (PDFs, images)
├── input_folder2/               # Additional test documents
├── results_folder/              # Parse & extract JSON output
├── groundings_folder/           # Visual grounding data
├── images/                      # Notebook documentation images
└── venv/                        # Python virtual environment
```

## 💡 Usage

### Core Workflow

The document processing pipeline consists of three main stages:

#### 1. Parse Documents

Converts PDFs/images into structured markdown with visual chunks:

```python
parse_result = client.parse(document=Path("invoice.pdf"))
# Returns: chunks, markdown, metadata, grounding
```

#### 2. Extract Structured Data

Applies a schema to extract specific fields:

```python
from landingai_ade.lib import pydantic_to_json_schema

schema = pydantic_to_json_schema(InvoiceExtractionSchema)
extract_result = client.extract(
    schema=schema,
    markdown=io.BytesIO(parse_result.markdown.encode("utf-8"))
)
# Returns: extraction (nested dict), extraction_metadata
```

#### 3. Save and Transform

Save results as JSON or transform to DataFrames:

```python
# Save both results
parse_result, extract_result = parse_extract_save(document_path, client, schema_class)

# Transform to database tables
invoice_summaries = create_invoice_summary_tables(parse_result, extract_result)
```

## 🛠️ API Functions

### `utilities.py`

#### `get_api_key() -> str`
Retrieves API key from environment variable.

#### `get_api_key_env() -> str`
Retrieves API key using Pydantic settings from `.env` file.

#### `save_parse_results(results, output_dir="./ade_results")`
Saves parse results to JSON file.

#### `parse_and_save(document_path, client, output_dir="./ade_results")`
Parses a document and saves results. Returns parse result object.

**Parameters:**
- `document_path`: Path to PDF/image file
- `client`: LandingAIADE client instance
- `output_dir`: Output directory for JSON

**Returns:** `ParseResponse`

#### `parse_extract_save(document_path, client, schema_class, output_dir="./ade_results")`
Complete pipeline: parse → extract → save both results.

**Parameters:**
- `document_path`: Path to PDF/image file
- `client`: LandingAIADE client instance
- `schema_class`: Pydantic schema class (e.g., `InvoiceExtractionSchema`)
- `output_dir`: Output directory for JSON files

**Returns:** `(parse_result, extract_result)` tuple

**Output Files:**
- `parse_{filename}.json`: Full parse result
- `extract_{filename}.json`: Structured extraction result

#### `create_invoice_summary_tables(results, extract_result=None, run_id=None)`
Converts parse/extract results into 4 pandas DataFrames matching Snowflake schema.

**Modes:**
- **Single document**: `create_invoice_summary_tables(parse_result, extract_result)`
- **Batch**: `create_invoice_summary_tables(results_list)` where `results_list = [(parse1, extract1), ...]`

**Returns:** List of 4 DataFrames:
1. **MARKDOWN**: Document-level markdown (1 row per document)
2. **PARSED_CHUNKS**: Individual chunks with grounding boxes (N rows per document)
3. **INVOICES_MAIN**: Flattened invoice fields (1 row per document)
4. **INVOICE_LINE_ITEMS**: Line item details (M rows per document)

## 📊 Data Pipeline

### Parse Result Structure

```json
{
  "chunks": [...],
  "markdown": "...",
  "metadata": {
    "filename": "invoice.pdf",
    "page_count": 1,
    "version": "dpt-2-20250919",
    "credit_usage": 3.0,
    "duration_ms": 7749
  },
  "splits": [...],
  "grounding": {...}
}
```

### Extract Result Structure

```json
{
  "extraction": {
    "invoice_info": {"invoice_number": "...", "invoice_date": "..."},
    "customer_info": {"sold_to_name": "..."},
    "company_info": {"supplier_name": "..."},
    "order_details": {"payment_terms": "..."},
    "totals_summary": {"total_due": 123.45},
    "line_items": [...]
  },
  "extraction_metadata": {...}
}
```

### Output DataFrames Schema

#### MARKDOWN Table
- RUN_ID, INVOICE_UUID, DOCUMENT_NAME, AGENTIC_DOC_VERSION, MARKDOWN

#### PARSED_CHUNKS Table
- RUN_ID, INVOICE_UUID, DOCUMENT_NAME, chunk_id, chunk_type, text, page, box_l, box_t, box_r, box_b

#### INVOICES_MAIN Table
- RUN_ID, INVOICE_UUID, DOCUMENT_NAME, AGENTIC_DOC_VERSION
- INVOICE_DATE_RAW, INVOICE_DATE, INVOICE_NUMBER, ORDER_DATE, PO_NUMBER, STATUS
- SOLD_TO_NAME, SOLD_TO_ADDRESS, CUSTOMER_EMAIL
- SUPPLIER_NAME, SUPPLIER_ADDRESS, REPRESENTATIVE, EMAIL, PHONE, GSTIN, PAN
- PAYMENT_TERMS, SHIP_VIA, SHIP_DATE, TRACKING_NUMBER
- CURRENCY, TOTAL_DUE_RAW, TOTAL_DUE, SUBTOTAL, TAX, SHIPPING, HANDLING_FEE

#### INVOICE_LINE_ITEMS Table
- RUN_ID, INVOICE_UUID, DOCUMENT_NAME, AGENTIC_DOC_VERSION, LINE_INDEX
- LINE_NUMBER, SKU, DESCRIPTION, QUANTITY, UNIT_PRICE, PRICE, AMOUNT, TOTAL

## 🗄️ Snowflake Integration

The project includes a complete Snowflake schema definition in `snowflake_setup.sql`:

### Tables

1. **MARKDOWN**: Full document markdown for inspection and RAG applications
2. **PARSED_CHUNKS**: Individual text/table chunks with bounding boxes
3. **INVOICES_MAIN**: Main invoice table (one row per invoice)
4. **INVOICE_LINE_ITEMS**: Line item details (multiple rows per invoice)

### Loading Data to Snowflake

```python
import snowflake.connector

# Create connection
conn = snowflake.connector.connect(
    user='your_user',
    password='your_password',
    account='your_account',
    warehouse='SNOWFLAKE_TUTORIALS',
    database='DEMOS_ADE_FINANCE',
    schema='INVOICES'
)

# Write DataFrames to Snowflake
from snowflake.connector.pandas_tools import write_pandas

write_pandas(conn, invoices_main_df, 'INVOICES_MAIN')
write_pandas(conn, line_items_df, 'INVOICE_LINE_ITEMS')
write_pandas(conn, chunks_df, 'PARSED_CHUNKS')
write_pandas(conn, markdown_df, 'MARKDOWN')
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Required
VISION_AGENT_API_KEY=your_api_key_here

# Optional - Batch Processing Settings
BATCH_SIZE=50                    # Number of files to process in parallel
MAX_WORKERS=2                    # Number of threads
MAX_RETRIES=5                    # Retry attempts for failed requests
MAX_RETRY_WAIT_TIME=30           # Max wait time between retries (seconds)
RETRY_LOGGING_STYLE=log_msg      # Logging style for retries
```

### Schema Customization

Edit `invoice_schema.py` to customize extraction fields:

```python
class DocumentInfo(BaseModel):
    invoice_date_raw: str = Field(..., description="Invoice date as string")
    invoice_date: Optional[date] = Field(..., description="Parsed date in YYYY-MM-DD")
    invoice_number: str = Field(..., description="Invoice number")
    # Add your custom fields here
```

**Important**: ADE supports **one level of nesting only**. Define nested models (like `DocumentInfo`, `CustomerInfo`) but don't nest them deeper.

## 📝 Supported File Formats

- ✅ PDF (`.pdf`)
- ✅ PNG (`.png`)
- ✅ JPEG (`.jpg`, `.jpeg`)

## 🤝 Contributing

This is a demonstration project. For production use cases, consider:

- Error handling and retry logic
- Rate limiting and throttling
- Validation of extracted data
- Monitoring and logging
- Cost tracking (credit usage)
- Data quality checks

## 📚 Resources

- [LandingAI ADE Documentation](https://docs.landing.ai/ade/ade-overview)
- [Visual Playground](https://va.landing.ai)
- [API Key Management](https://va.landing.ai/settings/api-key)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 📄 License

This project is provided as-is for demonstration purposes.

## 🆘 Support

For issues with:
- **LandingAI ADE**: Contact LandingAI support or consult documentation

---

**Built with [LandingAI](https://landing.ai)** 🤖
