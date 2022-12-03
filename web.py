from atexit import register
from email import feedparser
from urllib.robotparser import RequestRate
from flask import render_template, Flask,request
from werkzeug.utils import secure_filename
from io import BytesIO
from datetime import datetime
import os

import io
import pandas as pd
import docx2txt
from itertools import chain
import pdfplumber
import pytesseract
from PIL import Image
# from google.colab import files
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import regex as re
from gensim.utils import tokenize
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity



app=Flask(__name__,template_folder='templates',static_folder='static')
app.secret_key='ikstao'
APP_ROOT=os.path.dirname(os.path.abspath(__file__))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def create_path(filename):
    target = os.path.join(APP_ROOT,'static//images/')
    location = "events/".join([target, filename])
    return location

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))


@app.route('/',methods=['POST','GET'])
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST','GET'])
def upload():
    if request.method=='POST':
        jobDescription = request.files['jobDescription']
        if jobDescription:
            filename = secure_filename(jobDescription.filename)
            print(filename)
            target = os.path.join(APP_ROOT,'static/')
            destination = "job_des/".join([target, filename])
            jobDescription.save(destination)
            jobDescription = file_to_text(filename)
            # print(jobDescription)
        resume = request.files['resume']
        if resume:
            filename = secure_filename(resume.filename)
            print(filename)
            target = os.path.join(APP_ROOT,'static/')
            destination = "resume/".join([target, filename])
            resume.save(destination)
            resume = file_to_text(filename)
            cv = CountVectorizer(preprocessor=clean_text)
            resume = remove_links(resume)
            content = [jobDescription, resume] 
            mat = cv.fit_transform(content)
            sim_mat = cosine_similarity(mat)
            sim_per = round(sim_mat[0][1], 4) * 100
            print(sim_per)
            similarity=[]
            similarity.append(sim_per)
            similarity.append(100-sim_per)
            return render_template('stats.html', similarity=similarity)

    return render_template('upload.html')

##### EXTRA FUNCTIONS #####
def file_to_text(file_path):

    _, file_extension = os.path.splitext(file_path)

    if file_extension == ".docx":
        text = docx2txt.process(file_path).replace("\n","")
        return text

    elif file_extension == ".pdf":
      text = ""
      with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        for i in range(num_pages):
          page_content = pdf.pages[i].extract_text().replace("\n","")
          text += " "+page_content
      return text

    elif file_extension == ".txt":
      with open(file_path, "r") as f:
        text = f.read()
        text = text.replace("\n","")
      f.close()
      return text

    elif file_extension == ".JPG" or file_extension == ".JPEG" or file_extension == ".PNG":
      image = Image.open(file_path)
      text = pytesseract.image_to_string(image)
      text = text.replace("\n","")
      return text

    else:
      print("Unsupported Format.")

def remove_links(corpus):
        return re.sub(r'http\S+', '', corpus)

def clean_text(text):
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    tokens = list(tokenize(text))
    #res = ' '.join([stemmer.stem(t.lower()) for t in tokens if t.lower() not in stop_words]) 
    res = ' '.join([lemmatizer.lemmatize(t.lower()) for t in tokens if t.lower() not in stop_words]) 
    if len(res) == 0:
        return ' '
    else:
        return res
