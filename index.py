import nltk 
import math
from pymongo import MongoClient
from collections import defaultdict
from nltk.stem.snowball import EnglishStemmer # note: only works with English language

class Index: 
        """
        TO DO:
        - handle urls that no longer work 404 error
        """
        def __init__(self, corpus):
                self.client = MongoClient('localhost', 27017)
                self.db = self.client.index_db # index_db is the name of our database
                self.collection = self.db.entries
                self.corpus = corpus
                self.stemmer = EnglishStemmer()
                self.index = defaultdict(list)
                self.stopwords = nltk.corpus.stopwords.words('english')
                self.total_num_of_docs = 0 # used to calculate idf

        def print_index(self):
                for entry in self.collection.find():
                        print("id:", entry['_id'],'    ', 'postings:', entry['postings'])

        def search(self, query):
                """
                return: return a list of urls
                search for a query in the index
                results sorted by only by tf-idf score, need to implement cosine similarity
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
                                                for post in entry['postings']:
                                                        print(post)
                                                        directories.append( (post['doc_id'], post['tf_idf']) )
                                                result_directories |= set(directories) # union two sets

                # map each result directory/document to its corresponding link
                return sorted([(self.corpus.file_url_map[directory[0]],directory[1] )for directory in result_directories], key=lambda t: -t[1])   

        def remove_punctuation(self, text):
                punctuations = ['\\','`','*','_','{','}','[',']','(',')','>','<',
                                '#','+','-','.','!','$','\'','"',',',':','&','//',
                                '/',';','?','%','=','’']
                for p in punctuations:
                        if p in text:
                                text = text.replace(p, " ")
                return text

        def tokenize(self, text):
                """
                return: tuple->(dictionary->{token: num_of_occurances}, int->num_of_tokens)
                tokenizes the given string
                utilizes stemming and removes stopwords
                """
                num_of_tokens = 0 # used to calculate weighted term frequency
                tokens = defaultdict(int)
                text = self.remove_punctuation(text)
                for token in [tok.lower() for tok in nltk.word_tokenize(text)]:
                        if not token in self.stopwords:
                                token = self.stemmer.stem(token)
                                tokens[token] += 1
                                num_of_tokens += 1
                return (tokens, num_of_tokens)
        
        def add(self, tokens_tuple, directory):
                """
                takes a tokens_tuple (from a directory) which contains 2 items (dict,int).
                tuple content is desscribed further in tokenize() docstring
                adds a list of tokens to the inverted index 
                index format: { _id(token) => postings: [{'doc_id': '0/0', 'tf': 0.125, 'tf_id': -1}, {}] }
                where doc_id = directory 0/0
                where tf = num_of_occurances/num_of_tokens

                TO DO:
                 - Term frequency (raw count) DONE
                 - Term frequency (weighted/normalized) DONE
                 - Indices of occurrence within the document(optional)
                 - idf (raw count) DONE
                 - idf (weighted) DONE
                 - tf-idf score DONE
                """
                posting = { 'doc_id' : '', "tf" : -1, "tf_idf" : -1 }
                self.total_num_of_docs += 1 # used to calculate idf
                num_of_tokens = tokens_tuple[1]
                for token,num_of_occurances in tokens_tuple[0].items():
                        if directory not in self.index[token]:
                                weighted_tf = num_of_occurances/num_of_tokens
                                self.index[token].append([directory, weighted_tf])
                                posting['doc_id'] = directory
                                posting['tf'] = weighted_tf
                                self.collection.update({"_id": token}, {'$push': {'postings': posting}}, upsert = True)
                # for token in tokens_tuple[0].keys():
                #     print(token, self.index[token])

        def calculate_tf_idf(self):
                for entry in self.collection.find(): #iterate through entire index
                        df = len(entry['postings'])
                        idf = math.log10(self.total_num_of_docs/df)
                        for i in range(df):
                                tf = entry['postings'][i]['tf']
                                tf_idf = tf * idf
                                posting_location = "postings.{}.tf_idf".format(i)
                                self.collection.update({'_id': entry['_id']}, {'$set': { posting_location: tf_idf} }  )
                # self.print_index()