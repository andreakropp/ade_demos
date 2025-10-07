
from pathlib import Path
import json
import io
import uuid
import pandas as pd
from datetime import datetime

# Method 1: Environment variable
def get_api_key() -> str:
    import os

    key = os.environ.get("VISION_AGENT_API_KEY")
    if not key:
        raise ValueError(
            "API key not found. Please set the VISION_AGENT_API_KEY environment variable."
        )
    return key

# Method 2: From .env file with Pydantic settings
def get_api_key_env() -> str:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        vision_agent_api_key: str

        class Config:
            env_file = ".env"

    settings = Settings()
    return settings.vision_agent_api_key

def save_parse_results(results, output_dir: str = "./ade_results") -> None:
    """
    Save ADE parse results to disk.

    This function serializes a parse result object (such as the output from
    LandingAI's Agentic Document Extraction) into a JSON file and saves it to 
    the specified directory. The filename is derived from `results.metadata.filename`
    when available.

    Args:
        results: The ADE parse results object returned by the parse() call.
                 Must have `metadata.filename` and `model_dump()` attributes.
        output_dir (str, optional): Directory where the JSON file will be saved.
                                   Defaults to "./ade_results".

    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Use the filename embedded in the metadata
    parse_filename = getattr(getattr(results, "metadata", {}), "filename", "unknown_filename")
    base_filename = f"parse_{Path(parse_filename).stem}"

    # Dump results as JSON
    if hasattr(results, "model_dump"):
        results_json = json.dumps(results.model_dump(), indent=2, default=str)
    else:
        # fallback if it's a plain dict-like object
        results_json = json.dumps(results, indent=2, default=str)

    json_path = output_path / f"{base_filename}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(results_json)

    print(f"Parse results saved to: {json_path}")

def parse_and_save(document_path, client, output_dir: str = "./ade_results"):
    """
    Parse a document using LandingAI ADE and save the full result as JSON.

    This function takes a document filepath, sends it to the ADE parse API,
    and saves the complete parse result to disk. The JSON filename will match
    the original document filename.

    Args:
        document_path (str or Path): Path to the document file to parse.
                                     Supported formats: .pdf, .png, .jpg, .jpeg
        client (LandingAIADE): An initialized LandingAI ADE client instance.
        output_dir (str, optional): Directory where the JSON file will be saved.
                                   Defaults to "./ade_results".

    Returns:
        ParseResponse: The full parse result object from the ADE API.

    Raises:
        FileNotFoundError: If the document file does not exist.
        Exception: Any exceptions from the parse operation are propagated.

    Example:
        >>> from landingai_ade import LandingAIADE
        >>> from utilities import parse_and_save
        >>>
        >>> client = LandingAIADE(apikey="your-api-key")
        >>> result = parse_and_save("invoice.pdf", client, output_dir="./results")
        >>> print(f"Parsed {len(result.chunks)} chunks")
    """
    # Convert to Path object
    doc_path = Path(document_path)

    # Validate file exists
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Parse the document
    parse_result = client.parse(document=doc_path)

    # Save the results using existing function
    save_parse_results(parse_result, output_dir=output_dir)

    return parse_result

def parse_extract_save(document_path, client, schema_class, output_dir: str = "./ade_results"):
    """
    Parse a document, extract structured data using a Pydantic schema, and save both results as JSON.

    This function performs a complete ADE workflow:
    1. Parses the document to extract markdown and chunks
    2. Saves the parse result as parse_{filename}.json
    3. Extracts structured data using the provided Pydantic schema
    4. Saves the extraction result as extract_{filename}.json

    Args:
        document_path (str or Path): Path to the document file to parse.
                                     Supported formats: .pdf, .png, .jpg, .jpeg
        client (LandingAIADE): An initialized LandingAI ADE client instance.
        schema_class (BaseModel): A Pydantic model class defining the extraction schema.
        output_dir (str, optional): Directory where JSON files will be saved.
                                   Defaults to "./ade_results".

    Returns:
        tuple: (parse_result, extract_result) - Both result objects from the API.

    Raises:
        FileNotFoundError: If the document file does not exist.
        Exception: Any exceptions from parse or extract operations are propagated.

    Example:
        >>> from landingai_ade import LandingAIADE
        >>> from utilities import parse_extract_save
        >>> from invoice_schema import InvoiceExtractionSchema
        >>>
        >>> client = LandingAIADE(apikey="your-api-key")
        >>> parse_result, extract_result = parse_extract_save(
        ...     "my_doc.pdf",
        ...     client,
        ...     InvoiceExtractionSchema,
        ...     output_dir="./results"
        ... )
        >>> # Results saved as: parse_my_doc.json and extract_my_doc.json
        >>> print(f"Extracted: {extract_result.extraction}")
    """
    from landingai_ade.lib import pydantic_to_json_schema

    # Convert to Path object
    doc_path = Path(document_path)

    # Validate file exists
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract base filename without extension
    base_filename = doc_path.stem

    # STEP 1: Parse the document
    parse_result = client.parse(document=doc_path)

    # Save parse result
    parse_json_path = output_path / f"parse_{base_filename}.json"
    if hasattr(parse_result, "model_dump"):
        parse_json = json.dumps(parse_result.model_dump(), indent=2, default=str)
    else:
        parse_json = json.dumps(parse_result, indent=2, default=str)

    with open(parse_json_path, "w", encoding="utf-8") as f:
        f.write(parse_json)
    print(f"Parse results saved to: {parse_json_path}")

    # STEP 2: Extract structured data using the schema
    # Convert Pydantic schema to JSON schema
    json_schema = pydantic_to_json_schema(schema_class)

    # Call extract with markdown from parse result
    extract_result = client.extract(
        schema=json_schema,
        markdown=io.BytesIO(parse_result.markdown.encode("utf-8"))
    )

    # Save extract result
    extract_json_path = output_path / f"extract_{base_filename}.json"
    if hasattr(extract_result, "model_dump"):
        extract_json = json.dumps(extract_result.model_dump(), indent=2, default=str)
    else:
        extract_json = json.dumps(extract_result, indent=2, default=str)

    with open(extract_json_path, "w", encoding="utf-8") as f:
        f.write(extract_json)
    print(f"Extract results saved to: {extract_json_path}")

    return parse_result, extract_result

def create_invoice_summary_tables(results, extract_result=None, run_id=None):
    """
    Create 4 pandas DataFrames matching the Snowflake table structure from ADE parse and extract results.

    This function takes the parse and extraction results from LandingAI ADE and converts them into
    4 normalized pandas DataFrames that match the Snowflake schema:
    1. MARKDOWN - Full markdown output per document
    2. PARSED_CHUNKS - Individual chunks with grounding boxes
    3. INVOICES_MAIN - Flattened invoice-level fields (one row per invoice)
    4. INVOICE_LINE_ITEMS - Line items (multiple rows per invoice)

    Supports two modes:
    - **Single document mode**: Pass individual parse_result and extract_result
    - **Batch mode**: Pass a list of (parse_result, extract_result) tuples from parallel processing

    Args:
        results: Either:
                 - A ParseResponse object (single document mode), OR
                 - A list of (parse_result, extract_result) tuples (batch mode)
        extract_result: The ExtractResponse object (only for single document mode, ignored in batch mode)
        run_id (str, optional): Identifier for the processing batch/run. Defaults to generated UUID.

    Returns:
        list: invoice_summaries - List of 4 pandas DataFrames:
              [0] MARKDOWN DataFrame
              [1] PARSED_CHUNKS DataFrame
              [2] INVOICES_MAIN DataFrame
              [3] INVOICE_LINE_ITEMS DataFrame

    Examples:
        >>> # Single document mode:
        >>> from landingai_ade import LandingAIADE
        >>> from utilities import parse_extract_save, create_invoice_summary_tables
        >>> from invoice_schema import InvoiceExtractionSchema
        >>>
        >>> client = LandingAIADE(apikey="your-api-key")
        >>> parse_result, extract_result = parse_extract_save(
        ...     "invoice.pdf", client, InvoiceExtractionSchema, "./results"
        ... )
        >>> invoice_summaries = create_invoice_summary_tables(parse_result, extract_result)
        >>>
        >>> # Batch mode (from parallel processing):
        >>> results_summary = [(parse1, extract1), (parse2, extract2), ...]
        >>> invoice_summaries = create_invoice_summary_tables(results_summary)
        >>> # Returns 4 DataFrames with ALL documents combined
    """
    # Detect batch mode vs single document mode
    if isinstance(results, list):
        # Batch mode: results is a list of (parse_result, extract_result) tuples
        results_list = results
    else:
        # Single document mode: results is a single parse_result
        if extract_result is None:
            raise ValueError("In single document mode, extract_result parameter is required")
        results_list = [(results, extract_result)]

    # Generate common batch identifier
    if run_id is None:
        run_id = str(uuid.uuid4())

    # Initialize lists to accumulate data across all documents
    markdown_rows = []
    chunks_rows = []
    main_rows = []
    line_items_rows = []

    # Process each document
    for parse_result, extract_result in results_list:
        # Generate unique invoice UUID for this document
        invoice_uuid = str(uuid.uuid4())

        # Extract metadata from parse result
        document_name = parse_result.metadata.filename if hasattr(parse_result.metadata, 'filename') else 'unknown'
        agentic_doc_version = parse_result.metadata.version if hasattr(parse_result.metadata, 'version') else 'unknown'

        # ====================
        # TABLE 1: MARKDOWN
        # ====================
        markdown_rows.append({
            'RUN_ID': run_id,
            'INVOICE_UUID': invoice_uuid,
            'DOCUMENT_NAME': document_name,
            'AGENTIC_DOC_VERSION': agentic_doc_version,
            'MARKDOWN': parse_result.markdown
        })

        # ====================
        # TABLE 2: PARSED_CHUNKS
        # ====================
        for chunk in parse_result.chunks:
            # Extract grounding box coordinates
            grounding = chunk.grounding if hasattr(chunk, 'grounding') else None
            box = grounding.box if grounding and hasattr(grounding, 'box') else None
            page = grounding.page if grounding and hasattr(grounding, 'page') else None

            # Extract text from markdown (remove anchor tags and special markup)
            text = chunk.markdown if hasattr(chunk, 'markdown') else ''

            chunks_rows.append({
                'RUN_ID': run_id,
                'INVOICE_UUID': invoice_uuid,
                'DOCUMENT_NAME': document_name,
                'chunk_id': chunk.id if hasattr(chunk, 'id') else None,
                'chunk_type': chunk.type if hasattr(chunk, 'type') else None,
                'text': text,
                'page': page,
                'box_l': box.left if box and hasattr(box, 'left') else None,
                'box_t': box.top if box and hasattr(box, 'top') else None,
                'box_r': box.right if box and hasattr(box, 'right') else None,
                'box_b': box.bottom if box and hasattr(box, 'bottom') else None
            })

        # ====================
        # TABLE 3: INVOICES_MAIN
        # ====================
        extraction = extract_result.extraction if hasattr(extract_result, 'extraction') else {}

        # Helper to safely get nested dict values
        def safe_get(d, *keys):
            for key in keys:
                if isinstance(d, dict) and key in d:
                    d = d[key]
                else:
                    return None
            return d

        # Flatten all fields from the nested extraction schema
        main_data = {
            'RUN_ID': run_id,
            'INVOICE_UUID': invoice_uuid,
            'DOCUMENT_NAME': document_name,
            'AGENTIC_DOC_VERSION': agentic_doc_version,

            # DocumentInfo fields
            'INVOICE_DATE_RAW': safe_get(extraction, 'invoice_info', 'invoice_date_raw'),
            'INVOICE_DATE': safe_get(extraction, 'invoice_info', 'invoice_date'),
            'INVOICE_NUMBER': safe_get(extraction, 'invoice_info', 'invoice_number'),
            'ORDER_DATE': safe_get(extraction, 'invoice_info', 'order_date'),
            'PO_NUMBER': safe_get(extraction, 'invoice_info', 'po_number'),
            'STATUS': safe_get(extraction, 'invoice_info', 'status'),

            # CustomerInfo fields
            'SOLD_TO_NAME': safe_get(extraction, 'customer_info', 'sold_to_name'),
            'SOLD_TO_ADDRESS': safe_get(extraction, 'customer_info', 'sold_to_address'),
            'CUSTOMER_EMAIL': safe_get(extraction, 'customer_info', 'customer_email'),

            # SupplierInfo fields
            'SUPPLIER_NAME': safe_get(extraction, 'company_info', 'supplier_name'),
            'SUPPLIER_ADDRESS': safe_get(extraction, 'company_info', 'supplier_address'),
            'REPRESENTATIVE': safe_get(extraction, 'company_info', 'representative'),
            'EMAIL': safe_get(extraction, 'company_info', 'email'),
            'PHONE': safe_get(extraction, 'company_info', 'phone'),
            'GSTIN': safe_get(extraction, 'company_info', 'gstin'),
            'PAN': safe_get(extraction, 'company_info', 'pan'),

            # TermsAndShipping fields
            'PAYMENT_TERMS': safe_get(extraction, 'order_details', 'payment_terms'),
            'SHIP_VIA': safe_get(extraction, 'order_details', 'ship_via'),
            'SHIP_DATE': safe_get(extraction, 'order_details', 'ship_date'),
            'TRACKING_NUMBER': safe_get(extraction, 'order_details', 'tracking_number'),

            # TotalsSummary fields
            'CURRENCY': safe_get(extraction, 'totals_summary', 'currency'),
            'TOTAL_DUE_RAW': safe_get(extraction, 'totals_summary', 'total_due_raw'),
            'TOTAL_DUE': safe_get(extraction, 'totals_summary', 'total_due'),
            'SUBTOTAL': safe_get(extraction, 'totals_summary', 'subtotal'),
            'TAX': safe_get(extraction, 'totals_summary', 'tax'),
            'SHIPPING': safe_get(extraction, 'totals_summary', 'shipping'),
            'HANDLING_FEE': safe_get(extraction, 'totals_summary', 'handling_fee'),
        }

        main_rows.append(main_data)

        # ====================
        # TABLE 4: INVOICE_LINE_ITEMS
        # ====================
        line_items = safe_get(extraction, 'line_items') or []

        for idx, item in enumerate(line_items):
            line_items_rows.append({
                'RUN_ID': run_id,
                'INVOICE_UUID': invoice_uuid,
                'DOCUMENT_NAME': document_name,
                'AGENTIC_DOC_VERSION': agentic_doc_version,
                'LINE_INDEX': idx,
                'LINE_NUMBER': item.get('line_number') if isinstance(item, dict) else getattr(item, 'line_number', None),
                'SKU': item.get('sku') if isinstance(item, dict) else getattr(item, 'sku', None),
                'DESCRIPTION': item.get('description') if isinstance(item, dict) else getattr(item, 'description', None),
                'QUANTITY': item.get('quantity') if isinstance(item, dict) else getattr(item, 'quantity', None),
                'UNIT_PRICE': item.get('unit_price') if isinstance(item, dict) else getattr(item, 'unit_price', None),
                'PRICE': item.get('price') if isinstance(item, dict) else getattr(item, 'price', None),
                'AMOUNT': item.get('amount') if isinstance(item, dict) else getattr(item, 'amount', None),
                'TOTAL': item.get('total') if isinstance(item, dict) else getattr(item, 'total', None),
            })

    # Convert accumulated rows to DataFrames
    markdown_df = pd.DataFrame(markdown_rows)
    chunks_df = pd.DataFrame(chunks_rows)
    main_df = pd.DataFrame(main_rows)
    line_items_df = pd.DataFrame(line_items_rows)

    # Return all 4 tables as a list
    invoice_summaries = [markdown_df, chunks_df, main_df, line_items_df]

    return invoice_summaries