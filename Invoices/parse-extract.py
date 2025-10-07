# Import necessary libraries
import os
import io
import logging
from decimal import Decimal
from typing import Optional
from landingai_ade import LandingAIADE
from landingai_ade.lib import pydantic_to_json_schema
from pydantic import BaseModel, Field
import fitz  # pymupdf

DOCUMENT_PATH = "./wire-transfer.pdf"

def main():
    """Main execution function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Validate environment variable
    if not os.environ.get("VISION_AGENT_API_KEY"):
        raise ValueError("VISION_AGENT_API_KEY environment variable not set")

    # Validate document exists
    if not os.path.exists(DOCUMENT_PATH):
        raise FileNotFoundError(f"Document not found: {DOCUMENT_PATH}")

    # Validate file is a PDF
    if not DOCUMENT_PATH.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF: {DOCUMENT_PATH}")

    # Initialize the LandingAIADE client
    # It reads the API key from the VISION_AGENT_API_KEY environment variable
    client = LandingAIADE(
        apikey=os.environ.get(
            "VISION_AGENT_API_KEY"
        ),  # This is the default and can be omitted
    )

    # Parse the document from the specified path
    # The document can be a local file path or a remote URL
    try:
        response = client.parse(
            # support document as File or document_url as local path/remote url
            document_url=DOCUMENT_PATH,
            model="dpt-2-latest",
        )
    except Exception as e:
        logger.error(f"Failed to parse document: {e}")
        raise

    # Log the different parts of the parse response for debugging
    logger.info("--------RESPONSE-----------")
    logger.info(response)
    logger.info("--------RESPONSE.CHUNKS-----------")
    logger.info(response.chunks)
    logger.info("--------RESPONSE.MARKDOWN-----------")
    logger.info(response.markdown)
    logger.info("--------RESPONSE.METADATA-----------")
    logger.info(response.metadata)
    logger.info("--------RESPONSE.SPLITS-----------")
    logger.info(response.splits)

    # Define the data schema for extraction using Pydantic
    # This schema specifies what information to extract from the document
    class Invoice(BaseModel):
        description: str = Field(description="Invoice description")
        amount: Decimal = Field(description="Invoice Total amount")
        currency: Optional[str] = Field(default="USD", description="Currency code")

    # Convert the Pydantic model to a JSON schema
    # The extraction endpoint requires a JSON schema
    schema = pydantic_to_json_schema(Invoice)

    # Call the extract method with the generated markdown from the parse step
    # The markdown content is passed as a bytes object
    try:
        extract_response = client.extract(
            schema=schema,
            # support markdown as File or markdown_url as local path/remote url
            markdown=io.BytesIO(response.markdown.encode("utf-8")),
        )
    except Exception as e:
        logger.error(f"Failed to extract data: {e}")
        raise

    # Log the different parts of the extraction response for debugging
    logger.info("--------EXTRACTION RESPONSE-----------")
    logger.info(extract_response)
    logger.info("--------EXTRACTION RESPONSE.EXTRACTION-----------")
    logger.info(extract_response.extraction)
    logger.info("--------EXTRACTION RESPONSE.EXTRACTION_METADATA-----------")
    logger.info(extract_response.extraction_metadata)
    logger.info("--------EXTRACTION RESPONSE.METADATA-----------")
    logger.info(extract_response.metadata)

    # Get number of pages in the document
    try:
        with fitz.open(DOCUMENT_PATH) as doc:
            logger.info(f"Number of pages in {DOCUMENT_PATH}: {len(doc)} and it would cost {3 * len(doc)}")
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        raise

    # Count and log the number of characters in response.markdown
    num_chars_markdown = len(response.markdown)
    logger.info(f"Number of characters in response.markdown: {num_chars_markdown} and it would cost {round(num_chars_markdown/5000,1)}")
    # Count and log the number of characters in extract_response
    num_chars_extract_response = len(str(extract_response.extraction))
    logger.info(f"Number of characters in extract_response: {num_chars_extract_response} and it would cost {round(num_chars_extract_response/1000,1)}")
    logger.info(f"Total Extraction cost is {round(round(num_chars_markdown/5000,1)+round(num_chars_extract_response/1000,1),1)}")


if __name__ == "__main__":
    main()
