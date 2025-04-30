# app/documents/routes.py
import os
import datetime
import logging

from flask import (
    request,
    redirect,
    url_for,
    flash,
    render_template,
    current_app
)
from flask_login import login_required, current_user
from langchain.schema import Document as LC_Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.extensions import db
from app.models import UploadedDocument, Folder
from app.utils import update_user_vectorstore, scrape_website, simple_filter_metadata
from . import document_bp

# Try to import UnstructuredLoader
try:
    from langchain_unstructured import UnstructuredLoader as UnstructuredFileLoader
except ImportError:
    from langchain_community.document_loaders import UnstructuredFileLoader

logger = logging.getLogger(__name__)

# Upload Document
@document_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    # Retrieve uploaded file from the form
    file = request.files.get('document')
    if not file or not file.filename:
        flash('No file uploaded.')
        return redirect(url_for('dashboard'))

    # Check user directory exists
    user_dir = os.path.join('uploads', str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    path = os.path.join(user_dir, file.filename)

    # Save the file to the user's directory
    try:
        file.save(path)
    except Exception as e:
        logger.error('Error saving file: %s', e)
        flash('Error saving file.')
        return redirect(url_for('dashboard'))

    # Create a new UploadedDocument entry
    doc = UploadedDocument(
        filename=file.filename,
        file_type=file.filename.rsplit('.',1)[-1].lower(),
        user_id=current_user.id
    )
    try:
        db.session.add(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error('DB error on upload: %s', e)
        flash('Database error.')
        return redirect(url_for('dashboard'))

    # Process and index document
    try:
        loader = UnstructuredFileLoader(path)
        raw = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(raw)

        # Convert to LangChain Doucment objects and filter metadata
        processed = []
        for chunk in chunks:
            text = getattr(chunk, 'page_content', str(chunk))
            md   = getattr(chunk, 'metadata', {}) or {}
            processed.append(
                LC_Document(page_content=text,
                            metadata=simple_filter_metadata(md))
            )

        # Import embeddings and vectorstore classes  
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        from chromadb.config import Settings
        # Initialise embeddings with OpenAI API key
        emb = OpenAIEmbeddings(openai_api_key=current_app.config['OPENAI_API_KEY'])
        # Update the user's vectorstore with the processed documents
        update_user_vectorstore(
            current_user.id,
            processed,
            emb,
            Chroma,
            Settings
        )
    except Exception as e:
        logger.error('Error processing document: %s', e)
        flash('Document uploaded, but processing failed.')
        return redirect(url_for('dashboard'))
    # Notify user of success
    flash('Document uploaded and processed successfully!')
    return redirect(url_for('dashboard'))

# Scrape Website
@document_bp.route('/scrape', methods=['POST'])
@login_required
def scrape_document():
    # Get URL from form and validate
    url = request.form.get('url','').strip()
    if not url:
        flash('URL is required.')
        return redirect(url_for('dashboard'))
    # Get text from the URL
    text, error = scrape_website(url)
    if error:
        flash(error)
        return redirect(url_for('dashboard'))
    #Save scraped text to a .txt file
    user_dir = os.path.join('uploads', str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    fname = f"scraped_{datetime.datetime.utcnow():%Y%m%d%H%M%S}.txt"
    path = os.path.join(user_dir, fname)

    try:
        with open(path,'w',encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        logger.error('Error writing scraped file: %s', e)
        flash('Error writing scraped file.')
        return redirect(url_for('dashboard'))

    # Create a new UploadedDocument entry for the scraped file
    doc = UploadedDocument(filename=fname, file_type='txt', user_id=current_user.id)
    try:
        db.session.add(doc); db.session.commit()
    except Exception as e:
        db.session.rollback(); logger.error('DB error on scrape: %s', e); flash('Database error.'); return redirect(url_for('dashboard'))

    # Process scraped file into vectorstore
    try:
        loader = UnstructuredFileLoader(path)
        raw = loader.load()
        # Split the document into manageable chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(raw)
        # Convert to LangChain Document objects and filter metadata
        processed = []
        for chunk in chunks:
            text = getattr(chunk,'page_content',str(chunk))
            md   = getattr(chunk,'metadata',{}) or {}
            processed.append(LC_Document(page_content=text, metadata=simple_filter_metadata(md)))
        # Import embeddings and vectorstore classes    
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        from chromadb.config import Settings
        emb = OpenAIEmbeddings(openai_api_key=current_app.config['OPENAI_API_KEY'])
        # Update the user's vectorstore with the processed documents
        update_user_vectorstore(current_user.id, processed, emb, Chroma, Settings)
    except Exception as e:
        logger.error('Error processing scraped document: %s', e)
        flash('Website scraped, but processing failed.')
        return redirect(url_for('dashboard'))
    # Notify user of success
    flash('Website scraped and document processed successfully!')
    return redirect(url_for('dashboard'))

# Folder Management
@document_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    # Create a new folder for the user
    name = request.form.get('folder_name','').strip()
    if not name:
        flash('Folder name cannot be empty.')
        return redirect(url_for('dashboard'))
    if Folder.query.filter_by(user_id=current_user.id,name=name).first():
        flash('Folder already exists.')
        return redirect(url_for('dashboard'))
    f = Folder(name=name, user_id=current_user.id)
    try:
        db.session.add(f); db.session.commit(); flash('Folder created successfully!')
    except Exception as e:
        db.session.rollback(); logger.error('Error creating folder: %s', e); flash('Error creating folder.')
    return redirect(url_for('dashboard'))

@document_bp.route('/rename_folder/<int:folder_id>', methods=['POST'])
@login_required
def rename_folder(folder_id):
    # Rename an existing folder for the current user
    f = Folder.query.get_or_404(folder_id)
    if f.user_id != current_user.id:
        flash('Unauthorized access.'); return redirect(url_for('dashboard'))
    new_name = request.form.get('new_name','').strip()
    if not new_name:
        flash('New folder name cannot be empty.'); return redirect(url_for('dashboard'))
    f.name = new_name
    try:
        db.session.commit(); flash('Folder renamed successfully!')
    except Exception as e:
        db.session.rollback(); logger.error('Error updating folder name: %s', e); flash('Error updating folder name.')
    return redirect(url_for('dashboard'))

@document_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    # Delete a folder and unassign its documents
    f = Folder.query.get_or_404(folder_id)
    if f.user_id != current_user.id:
        flash('Unauthorized access.'); return redirect(url_for('dashboard'))
    # Unassign documents from the folder
    for doc in UploadedDocument.query.filter_by(folder_id=f.id): doc.folder_id=None
    try:
        db.session.delete(f); db.session.commit(); flash('Folder deleted successfully! Documents have been unassigned.')
    except Exception as e:
        db.session.rollback(); logger.error('Error deleting folder: %s', e); flash('Error deleting folder.')
    return redirect(url_for('dashboard'))

@document_bp.route('/folder/<int:folder_id>')
@login_required
def view_folder(folder_id):
    # Show contents of a specific folder
    f=Folder.query.get_or_404(folder_id)
    if f.user_id!=current_user.id: flash('Unauthorized access.'); return redirect(url_for('dashboard'))
    docs=UploadedDocument.query.filter_by(folder_id=f.id).all()
    return render_template('folder.html', folder=f, documents=docs)

@document_bp.route('/update_folder/<int:doc_id>', methods=['POST'])
@login_required
def update_folder(doc_id):
    # Change the folder assignment for a document
    d=UploadedDocument.query.get_or_404(doc_id)
    if d.user_id!=current_user.id: flash('Unauthorized access.'); return redirect(url_for('dashboard'))
    fid=request.form.get('folder_id')
    d.folder_id=None if not fid or fid=='0' else int(fid)
    try:
        db.session.commit(); flash('Folder updated successfully!')
    except Exception as e:
        db.session.rollback(); logger.error('Error updating document\'s folder: %s', e); flash('Error updating folder.')
    return redirect(url_for('dashboard'))

@document_bp.route('/delete_document/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    # Delete a document and its associated file
    d=UploadedDocument.query.get_or_404(doc_id)
    if d.user_id!=current_user.id: flash('Unauthorized access.'); return redirect(url_for('dashboard'))
    # delete file from uploads folder directory
    p=os.path.join('uploads',str(current_user.id),d.filename)
    try:
        if os.path.exists(p): os.remove(p)
    except Exception as e:
        logger.error('Error deleting file from disk: %s',e)
    # Delete document from DB
    try:
        db.session.delete(d); db.session.commit(); flash('Document deleted successfully!')
    except Exception as e:
        db.session.rollback(); logger.error('Error deleting document from DB: %s',e); flash('Error deleting document.')
    return redirect(url_for('dashboard'))
