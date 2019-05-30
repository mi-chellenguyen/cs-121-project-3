from flask import Flask, request, render_template
import os
from corpus import Corpus
from bs4 import BeautifulSoup
from lxml import html
from index import Index
from urllib.request import urlopen

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/results')
def results():
    query = request.args.get("query")
    results = search(query)
    top_results = top_search(results)
    return render_template("results.html", query_param = query, results = top_results)

def search(query: str):
    print("You searched for:", query)
    results = index.search(query)
    print ("The query: '" + query +"' is found in these links: ", results)
    return results

def top_search(results: []):
	#returns tuple list (link, title, content)
	#restricted to 100 searches for time
    corpus = Corpus()
    top_results = []
    count = 0
    for link, score in results:
        count+=1
        try:
            file_addr = corpus.get_file_name("https://"+link)

            content_tree = html.parse(file_addr)
            try:
                content_string = html.tostring(content_tree)
            except:
                content_string = ''
            soup = BeautifulSoup(content_string,"lxml")
            title = soup.title.string
            content = ""
            meta = soup.find_all('meta')
            for tag in meta:
                if 'name' in tag.attrs.keys() and tag.attrs['name'].strip().lower() == 'description':
                    content = tag.attrs['content']
            top_results.append((link, title, content))
            """print(link, title, content)"""
        except:
            top_results.append((link, link, ""))
        if count ==100:
            break
    return top_results
    

def create_index(reset=False):
    """
    return: Index object
    creates an inverted index from corpus
    """
    corpus = Corpus()
    index = Index(corpus)
    counter = 1

    if reset:
        print("Reset parameter =", reset, ". Deleting all rows from index.")
        index.collection.delete_many({}) # all rows from collection entries
         # go through all directories in the corpus (0/0, 0/1, 0/2...) => folder 0, file 0 in WEBPAGES_RAW
        for directory in corpus.file_url_map:
            # get file content
            folder,file = directory.split("/") #0/10 => folder = 0, file = 10
            # print("FOLDER: {}, FILE: {}".format(folder,file))
            file_addr = os.path.join(".", corpus.WEBPAGES_RAW_NAME, folder, file)
            content_tree = html.parse(file_addr)
            try:
                content_string = html.tostring(content_tree)
            except:
                content_string = ''
    
            # use BeautifulSoup to parse HTML to remove HTML tags, resulting in just text
            soup = BeautifulSoup(content_string, 'lxml')
            text = soup.text
    
            # create tokens
            tokens_tuple = index.tokenize(text)
    
            # add tokens to index
            index.add(tokens_tuple, directory)
            
            # remove if want to create index on ALL documents in corpus
            #############################
            # if counter == 10: # will only go through first 10 documents
            #     break
            # counter += 1
            #############################
        # index.calculate_tf_idf()   print("db is reset, starting to create index...")

    return index

if __name__ == '__main__':
    index = create_index()
    print("Index Created")
    app.run(debug=False)
    