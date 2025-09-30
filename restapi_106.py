"""
REST API Lab Submission - Book Catalog API
Roll Number: 106
Topic: Simple Book Catalog API (Roll Number % 3 == 1)

This API manages a book catalog with CRUD operations using FastAPI.
Data is stored in an in-memory dictionary acting as a simple database.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title="Book Catalog API",
    description="A REST API for managing book catalog",
    version="1.0.0"
)

# Pydantic models for request/response validation
class Book(BaseModel):
    """Model for book data with validation"""
    title: str
    author: str
    isbn: str
    publication_year: int
    genre: str
    available: bool = True

class BookUpdate(BaseModel):
    """Model for partial book updates - all fields optional"""
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    available: Optional[bool] = None

# In-memory database (dictionary) to store books
# Key: book_id (int), Value: Book data (dict)
books_db: Dict[int, dict] = {
    1: {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "isbn": "978-0-06-112008-4",
        "publication_year": 1960,
        "genre": "Fiction",
        "available": True
    },
    2: {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "978-0-452-28423-4",
        "publication_year": 1949,
        "genre": "Dystopian",
        "available": True
    }
}

# Counter for generating unique book IDs
next_book_id = 3


# ============== GET ENDPOINTS ==============

@app.get("/")
def root():
    """Root endpoint - API welcome message"""
    return {
        "message": "Welcome to Book Catalog API",
        "endpoints": {
            "GET /books": "Get all books",
            "GET /books/{book_id}": "Get specific book",
            "POST /books": "Add new book",
            "PUT /books/{book_id}": "Update book",
            "DELETE /books/{book_id}": "Delete book"
        }
    }


@app.get("/books", status_code=status.HTTP_200_OK)
def get_all_books(genre: Optional[str] = None, available: Optional[bool] = None):
    """
    GET endpoint - Retrieve all books from the catalog
    
    Query Parameters:
    - genre (optional): Filter books by genre
    - available (optional): Filter by availability status
    
    Returns: List of all books or filtered books
    """
    if not books_db:
        return {"message": "No books in catalog", "books": []}
    
    # Filter books based on query parameters
    filtered_books = books_db.copy()
    
    if genre:
        filtered_books = {
            k: v for k, v in filtered_books.items() 
            if v["genre"].lower() == genre.lower()
        }
    
    if available is not None:
        filtered_books = {
            k: v for k, v in filtered_books.items() 
            if v["available"] == available
        }
    
    # Format response with book IDs
    result = [{"id": book_id, **book_data} for book_id, book_data in filtered_books.items()]
    
    return {
        "total_books": len(result),
        "books": result
    }


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
def get_book(book_id: int):
    """
    GET endpoint - Retrieve a specific book by ID
    
    Path Parameter:
    - book_id: Unique identifier for the book
    
    Returns: Book details
    Raises: 404 if book not found
    """
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    return {
        "id": book_id,
        **books_db[book_id]
    }


# ============== POST ENDPOINT ==============

@app.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(book: Book):
    """
    POST endpoint - Add a new book to the catalog
    
    Request Body: Book object with title, author, isbn, publication_year, genre
    
    Returns: Created book with assigned ID
    """
    global next_book_id
    
    # Check if ISBN already exists
    for existing_book in books_db.values():
        if existing_book["isbn"] == book.isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN {book.isbn} already exists"
            )
    
    # Add book to database
    book_id = next_book_id
    books_db[book_id] = book.model_dump()
    next_book_id += 1
    
    return {
        "message": "Book created successfully",
        "book": {
            "id": book_id,
            **books_db[book_id]
        }
    }


# ============== PUT ENDPOINT ==============

@app.put("/books/{book_id}", status_code=status.HTTP_200_OK)
def update_book(book_id: int, book_update: BookUpdate):
    """
    PUT endpoint - Update an existing book's information
    
    Path Parameter:
    - book_id: ID of the book to update
    
    Request Body: BookUpdate object with optional fields to update
    
    Returns: Updated book details
    Raises: 404 if book not found
    """
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Update only the fields that are provided
    update_data = book_update.model_dump(exclude_unset=True)
    
    # Check if updating ISBN and if it conflicts with another book
    if "isbn" in update_data:
        for bid, bdata in books_db.items():
            if bid != book_id and bdata["isbn"] == update_data["isbn"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ISBN {update_data['isbn']} already exists for another book"
                )
    
    # Apply updates
    books_db[book_id].update(update_data)
    
    return {
        "message": "Book updated successfully",
        "book": {
            "id": book_id,
            **books_db[book_id]
        }
    }


# ============== DELETE ENDPOINT ==============

@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int):
    """
    DELETE endpoint - Remove a book from the catalog
    
    Path Parameter:
    - book_id: ID of the book to delete
    
    Returns: Success message with deleted book info
    Raises: 404 if book not found
    """
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Store book info before deletion
    deleted_book = books_db[book_id].copy()
    
    # Delete the book
    del books_db[book_id]
    
    return {
        "message": "Book deleted successfully",
        "deleted_book": {
            "id": book_id,
            **deleted_book
        }
    }


# Run the application
if __name__ == "__main__":
    # Start the FastAPI server on localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)