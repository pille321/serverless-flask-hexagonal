import abc
import os
from abc import abstractmethod

import boto3
from flask import jsonify, Flask, request


class Book:
    def __init__(self, book_id: str = "", title: str = ""):
        self.book_id = book_id
        self.title = title


class BookPort:
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def save(self, book: Book) -> Book:
        pass

    @abstractmethod
    def find(self, book_id: str) -> Book:
        pass


class BooksDynamoDBAdapter(BookPort):
    BOOKS_TABLE = os.environ['BOOKS_TABLE']

    def __init__(self):
        self.client = boto3.client('dynamodb')

    def save(self, book: Book) -> Book:
        resp = self.client.put_item(
            TableName=self.BOOKS_TABLE,
            Item={
                'bookId': {'S': book.book_id},
                'title': {'S': book.title}
            }
        )

        return book

    def find(self, book_id: str) -> Book:
        resp = self.client.get_item(
            TableName=self.BOOKS_TABLE,
            Key={
                'bookId': {'S': book_id}
            }
        )
        item = resp.get('Item')
        if not item:
            return Book()

        return Book(item.get('bookId').get('S'), item.get('title').get('S'))


class TestAdapter(BookPort):

    def __init__(self):
        self.client = print

    def save(self, book: Book) -> Book:
        self.client(book)

        return book

    def find(self, book_id: str) -> Book:
        return Book("test", "test")


class BooksUseCase:
    def __init__(self, book_port):
        self.db_port = book_port

    def save(self, book) -> Book:
        return self.db_port.save(book)

    def get(self, book_id) -> Book:
        return self.db_port.find(book_id)


app = Flask(__name__)
app.config["DEBUG"] = True

usecase = BooksUseCase(book_port=BooksDynamoDBAdapter())


@app.route("/api/v1/book/<string:book_id>")
def get_book(book_id):
    item = usecase.get(book_id)
    if not item:
        return jsonify({'error': 'Book does not exist'}), 404

    return jsonify({
        'bookId': item.book_id,
        'title': item.title
    })


@app.route("/api/v1/book", methods=["POST"])
def creat_book():
    book_id = request.json.get('bookId')
    title = request.json.get('title')
    if not book_id or not title:
        return jsonify({'error': 'Please provide bookId and title'}), 400

    book = usecase.save(Book(book_id, title))

    return jsonify({
        'bookId': book.book_id,
        'title': book.title
    })
