import mongo_setup as mongo_setup
from flask import Flask, request, render_template

import os
import json
import nltk 
import string
from collections import defaultdict
from nltk.stem.snowball import EnglishStemmer # note: only works with English language
from corpus import Corpus
from bs4 import BeautifulSoup
from lxml import html
from index import Index

app = Flask(__name__)

# maps index_entry.html to python function index_entry()
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/results')
def results():
    query = request.args.get("query")
    results = search(query)
    return render_template("results.html", query_param = query, results = results)

def search(query: str):
    print("You searched for:", query)
    results = index.search(query)
    print ("The query: '" + query +"' is found in these links: ", results)
    # do search in db
    return results

def main():
    #mongo_setup.global_init()
    pass

def create_index():
        """
        return: Index object
        creates an inverted index from corpus
        search only does bool retrieval (not ranked retrieval)
        """
        corpus = Corpus()
        index = Index(corpus)
        counter = 1
        # go through all directories in the corpus (0/0, 0/1, 0/2...) => folder 0, file 0 in WEBPAGES_RAW
        for directory in corpus.file_url_map:
                # get file content
                folder,file = directory.split("/") #0/10 => folder = 0, file = 10
                # print("FOLDER: {}, FILE: {}".format(folder,file))
                file_addr = os.path.join(".", corpus.WEBPAGES_RAW_NAME, folder, file)
                content_tree = html.parse(file_addr)
                content_string = html.tostring(content_tree)

                # use BeautifulSoup to parse HTML to remove HTML tags, resulting in just text
                soup = BeautifulSoup(content_string, 'lxml')
                text = soup.text
        
                # create tokens
                tokens = index.tokenize(text)
        
                # add tokens to index
                index.add(tokens, text, directory)

                if counter == 100:
                        break
                counter += 1
        return index

if __name__ == '__main__':
    # main()
    index = create_index()
    print("Index Created")
    app.run(debug=True)