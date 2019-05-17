import os
import json
import nltk 
import string
from collections import defaultdict
from nltk.stem.snowball import EnglishStemmer # note: only works with English language
from corpus import Corpus
from bs4 import BeautifulSoup
from lxml import html

class Index: 
        """
        TO DO:
        - postings to contain more info (i.e. tf-idf)
        - handle urls that no longer work 404 error
        """
        def __init__(self, corpus):
                self.corpus = corpus
                self.stemmer = EnglishStemmer()
                self.index = defaultdict(list)
                self.stopwords = nltk.corpus.stopwords.words('english')
        
        def search(self, query):
                """
                return: return a list of urls
                search for a query in the index
                TO DO:
                - implement searching for multi-word queries DONE
                - splits query by spaces for now (how to handle things like commas in query)
                - rank by cosine similarity
                """
                result_directories = set()
                query_list = query.lower().split()
                try:
                    for word in query_list:
                        if not word in self.stopwords:
                            word = self.stemmer.stem(word)
                            directories = []
                            for posting in self.index.get(word): # posting = [directory,num_of_occurances]; posting[0] = directory, posting[1] = num_of_occurances
                                  directories.append(posting[0])
                            result_directories |= set(directories) # union the two sets
                    # print("result directories",result_directories)
                    # map each result directory/document to its corresponding link
                    return [self.corpus.file_url_map[directory] for directory in result_directories]  
                except:
                    return []     

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
                return: dictionary {token: num_of_occurances}
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
        
        def add(self, tokens, document, directory):
                """
                adds a list of tokens to the inverted index 
                index format: token => [ [doc_id, num_of_occurances], [doc2, 5] ]
                where doc_id = directory 0/0

                TO DO:
                 - Term frequency (raw count) DONE
                 - Term frequency (weighted/normalized)
                 - Indices of occurrence within the document
                 - idf (raw count)
                 - idf (weighted)
                 - tf-idf score
                """
                for token,occurances in tokens.items():
                        if directory not in self.index[token]:
                                self.index[token].append([directory,occurances])
                
                # for token in tokens.keys():
                #     print(token, self.index[token])