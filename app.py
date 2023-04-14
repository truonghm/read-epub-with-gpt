import os
import tempfile
import ebooklib
from ebooklib import epub
import streamlit as st
import shutil
from bs4 import BeautifulSoup
import openai
import math
import random
import time

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PAGE_SIZE = 2000


def read_epub_content(epub_file):
    book = epub.read_epub(epub_file)
    html_items = ""

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            html_content = item.get_content().decode("utf-8", "ignore")
            soup = BeautifulSoup(html_content, "html.parser")
            html_items += str(soup)

    final_html = BeautifulSoup(html_items, "html.parser")

    return final_html


def divide_into_pages(final_html, screen_size):
    passage_elements = final_html.find_all(["p", "div", "section"])

    pages = []
    current_page = ""
    current_chars = 0

    for element in passage_elements:
        element_str = str(element)

        if current_chars + len(element_str) > PAGE_SIZE:
            pages.append(current_page)
            current_page = ""
            current_chars = 0

        current_page += element_str
        current_chars += len(element_str)

    if current_page:
        pages.append(current_page)

    return pages


def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (openai.error.RateLimitError,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper


@retry_with_exponential_backoff
def summary_generator(message):
    openai.api_key = OPENAI_API_KEY
    messages = [
        {
            "role": "system",
            "content": """
        You are a helpful English translator. 
        You take input as texts from a book, you respond with a summary of the texts.
        Keep the text consise, and format it with bullet points wherever possible.
        If the text is too short, you can skip it. 
        Respond only with the summary. 
        Never introduce or explain yourself.
        """,
        },
        {"role": "user", "content": message},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=messages,
    )

    return response.choices[0].message.content.strip()


def main():
    st.title("Read ePub and Summarize simultaneously!")

    uploaded_file = st.file_uploader("Upload an ePub file", type="epub")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as f:
            f.write(uploaded_file.getvalue())
            html_items = read_epub_content(f.name)
            os.unlink(f.name)

        pages = divide_into_pages(html_items, "medium")
        page_number = st.number_input(
            "Page Number", min_value=1, max_value=len(pages), value=1
        )
        st.write("Total Pages:", len(pages))

        page = pages[page_number - 1]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(page, unsafe_allow_html=True)

        with col2:
            message = BeautifulSoup(page, "html.parser").text

            response_text = summary_generator(message)
            # response_text = "Hello"
            st.markdown(response_text)
    else:
        st.warning("Please upload an ePub file.")


if __name__ == "__main__":
    main()
