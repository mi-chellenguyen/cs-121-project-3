import nltk 
import math
import re
from pprint import pprint
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from collections import defaultdict
from nltk.stem.snowball import EnglishStemmer # note: only works with English language 

class Index: 
    """
    TO DO:
    - handle urls that no longer work 404 error
    - use a more complex regular expression pattern for removing punctuations
    """
    def __init__(self, corpus):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.index_db # index_db is the name of our database
        self.collection = self.db.entries
        self.corpus = corpus
        self.stemmer = EnglishStemmer()
        self.stopwords = nltk.corpus.stopwords.words('english')
        self.total_num_of_docs = 0 # used to calculate idf

    def print_index(self):
        """
        prints everything in index
        useful for debugging
        """
        for entry in self.collection.find():
            print("id: {:20} postings: {}".format( entry['_id'], entry['postings']))

    def remove_punctuation(self, text):
        return re.sub('[^a-zA-Z0-9]', ' ', text)

    def tokenize(self, text):
        """
        return: tuple->(dictionary->{token: num_of_occurances})
        tokenizes the given string
        utilizes stemming and removes stopwords
        """
        tokens = defaultdict(int)
        text = self.remove_punctuation(text)
        for token in [tok.lower() for tok in nltk.word_tokenize(text)]:
            if not token in self.stopwords:
                token = self.stemmer.stem(token)
                tokens[token] += 1
        return tokens
    
    def add(self, tokens, directory):
        """
        takes a tokens_tuple (from a directory) which contains 2 items (dict,int).
        tuple content is desscribed further in tokenize() docstring
        adds a list of tokens to the inverted index 
        index format: { _id(token) => postings: [{'doc_id': '0/0', 'tf': 0.125, 'tf_id': -1}, {...}] }
        where doc_id = directory 0/0
        where tf = num_of_occurances/num_of_tokens

        TO DO:
            - Term frequency (raw count) DONE
            - Indices of occurrence within the document(optional)
            - df (raw count) DONE
            - idf (weighted) DONE
            - tf-idf score DONE
            - bulk insert (optimization) DONE
        """
        db_requests = []
        posting = { 'doc_id' : '', "tf" : -1, "tf_idf" : -1 }
        self.total_num_of_docs += 1 # used to calculate idf
        for token,num_of_occurances in tokens.items():
            posting['doc_id'] = directory
            posting['tf'] = num_of_occurances
            request = UpdateOne({"_id": token}, {'$push': {'postings': posting}}, upsert = True)
            db_requests.append(request)
        try:
            if db_requests:
                self.collection.bulk_write(db_requests)
            else:
                print("directory had no tokens:", directory)
        except BulkWriteError as bwe:
            print("error adding tokens from directory:", directory)
            pprint(bwe.details)
    
    def search(self, query):
        """
        return: return a list of urls
        search for a query in the index
        will calculate tf-idf score for each query token if it has not been done yet
        TO DO:
        - implement searching for multi-word queries DONE
        - splits query by spaces for now (how to handle things like commas in query)
        - rank by cosine similarity
        """
        
        result_directories = set()
        query_list = query.lower().split()
        for word in query_list:
            if not word in self.stopwords:
                word = self.stemmer.stem(word)
                directories = []
                entry = self.collection.find_one({'_id': word})
                if entry:
                    if entry['postings'][0]['tf_idf'] == -1: # if tf-idf for a specific token has not been calculated yet
                        self.calculate_tf_idf(entry)
                        entry = self.collection.find_one({'_id': word}) # db modified

                    for post in entry['postings']:
                        directories.append( (post['doc_id'], post['tf_idf']) )
                    result_directories |= set(directories) # union two sets
        # map each result directory/document to its corresponding link
        return sorted([(self.corpus.file_url_map[directory[0]],directory[1] )for directory in result_directories], key=lambda t: -t[1])   

    def calculate_tf_idf(self, entry):
        df = len(entry['postings'])
        #can't log (0) so initialize idf to a large negative number
        idf = -1000
        if  ( not self.total_num_of_docs == 0):
            idf = math.log10(self.total_num_of_docs/df)
        db_requests = []
        for i in range(df):
            tf = 1 + math.log10(entry['postings'][i]['tf'])
            tf_idf = tf * idf
            posting_location = "postings.{}.tf_idf".format(i)
            request = UpdateOne({'_id': entry['_id']}, {'$set': { posting_location: tf_idf} }  )
            db_requests.append(request)
        try:
            self.collection.bulk_write(db_requests)
        except BulkWriteError as bwe:
            print("error writing to db in calculate_tf_idf():")
            pprint(bwe.details)


        ######################## Calculated tf-idf for every entry in the index ############################
        # for entry in self.collection.find(): #iterate through entire index
        #     df = len(entry['postings'])
        #     idf = math.log10(self.total_num_of_docs/df)
        #     db_requests = []
        #     for i in range(df):
        #         tf = 1 + math.log10(entry['postings'][i]['tf'])
        #         tf_idf = tf * idf
        #         posting_location = "postings.{}.tf_idf".format(i)
        #         request = UpdateOne({'_id': entry['_id']}, {'$set': { posting_location: tf_idf} }  )
        #         db_requests.append(request)
        #     try:
        #         self.collection.bulk_write(db_requests)
        #     except BulkWriteError as bwe:
        #         print("error writing to db in calculate_tf_idf():")
        #         pprint(bwe.details)