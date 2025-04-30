# app/utils.py
import os
import logging
import warnings
import pypandoc
import nltk
from langchain.schema import Document

# Logging config
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Ensure pandoc executable is discoverable for pypandoc
def setup_pandoc():
    os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')
    os.environ['PYPANDOC_PANDOC'] = '/opt/homebrew/bin/pandoc'
    try:
        version = pypandoc.get_pandoc_version()
        logger.info('Pandoc version: %s', version)
    except Exception as e:
        logger.error('Error getting pandoc version: %s', e)


# Download NLTK resources if not already present
def initialize_nltk_resources():
    # Mapping of NLTK packages to their resource paths
    resource_map = {
        'punkt': 'tokenizers/punkt',
        'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger'
    }
    for pkg, path in resource_map.items():
        try:
            # Check if the resource is already downloaded
            nltk.data.find(path)
        except LookupError:
            # If not, download the package
            logger.info('Downloading NLTK package: %s', pkg)
            nltk.download(pkg, quiet=True)


# Strip metadata values to simple JSON-serialisable types
def simple_filter_metadata(metadata: dict) -> dict:
    return {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}

# Return Chroma client settings for a user's persistent vector DB
def get_client_settings_for_user(user_id, Settings):
    # Create a directory for the user's vector store if it doesn't exist
    persist_dir = os.path.join('chroma_db', f'user_{user_id}_db')
    os.makedirs(persist_dir, exist_ok=True)
    # Return initialised settings
    return Settings(
        persist_directory=persist_dir,
        anonymized_telemetry=False
    )

# Create or update a Chroma vector store for the given user and documents
def update_user_vectorstore(user_id, docs, embeddings, Chroma, Settings):
    # Get or create the vector store settings
    settings = get_client_settings_for_user(user_id, Settings)
    collection_name = f'user_{user_id}'
    # Convert documents to a list of Document objects
    filtered = []
    for doc in docs:
        content = getattr(doc, 'page_content', str(doc))
        md = getattr(doc, 'metadata', {}) or {}
        filtered.append(Document(page_content=content, metadata=simple_filter_metadata(md)))

    # create or open the collection
    vs = Chroma(
        persist_directory=settings.persist_directory,
        embedding_function=embeddings,
        client_settings=settings,
        collection_name=collection_name
    )

    if filtered:
        try:
            # Add new texts to the vectorstore
            vs.add_texts(
                [d.page_content for d in filtered],
                metadatas=[d.metadata for d in filtered]
            )
            logger.info('Vectorstore updated for user %s with %s chunks.', user_id, len(filtered))
        except Exception as e:
            # If add_texts fails, we need to rebuild the vectorstore from scratch
            logger.error('Chroma add_texts failed, rebuilding from scratch: %s', e)
            vs = Chroma.from_documents(
                filtered,
                embeddings,
                client_settings=settings,
                collection_name=collection_name
            )
    else:
        # If no documents are provided, we return empty vectorstore
        logger.info('No documents found for user %s; returning empty vectorstore.', user_id)

    return vs

# Scrape page text via requests + BeautifulSoup, returning concatenated <p> tags.
def scrape_website(url):
    import requests
    from bs4 import BeautifulSoup

    headers = {'User-Agent': 'MyRAGApp/1.0'}
    try:
        # Fetch the page with timeout
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        # Handle request errors
        logger.error('Error fetching URL: %s', e)
        return None, f'Error fetching URL: {e}'

    # Parse the HTML content
    soup = BeautifulSoup(resp.text, 'html.parser')
    paragraphs = soup.find_all('p')
    text = '\n'.join(p.get_text() for p in paragraphs)

    if not text.strip():
        # Handle case where no text is found
        logger.warning('No text found on the page.')
        return None, 'No text found on the page.'

    return text, None