# -*- coding: utf-8 -*-
"""
Created on Sat Jan 12 15:49:55 2019

@author: ABHISEK
"""

from flask import Flask,request, make_response,send_file
import pandas as pd
import numpy as np
import nltk
#nltk.download("stopwords")
from sklearn.feature_extraction.text import CountVectorizer
import re
from nltk.corpus import stopwords
from io import BytesIO
import time
import zipfile
from sklearn.cluster import KMeans
from flasgger import Swagger

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3
}
# you have to swaggify the app
swagger = Swagger(app)

stop = set(stopwords.words('english')) #set of stopwords
sno = nltk.stem.SnowballStemmer('english') #initialising the snowball stemmer

def cleanhtml(sentence): #function to clean the word of any html-tags
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', sentence)
    return cleantext


def cleanpunc(sentence): #function to clean the word of any punctuation or special characters
    cleaned = re.sub(r'[?|!|\'|"|#]',r'',sentence)
    cleaned = re.sub(r'[.|,|)|(|\|/]',r' ',cleaned)
    return  cleaned


def cleantext(text):
    str1=' '
    final_string=[]
    s=''
    for sent in text:
        filtered_sentence=[]
        sent=cleanhtml(sent) # remove HTMl tags
        for w in sent.split():
            for cleaned_words in cleanpunc(w).split():
                if((cleaned_words.isalpha()) & (len(cleaned_words)>2) & (cleaned_words not in stop)):    
                    s=(sno.stem(cleaned_words.lower())).encode('utf-8')
                    filtered_sentence.append(s)
                else:
                    continue 
        str1 = b" ".join(filtered_sentence) #final string of cleaned words    
        final_string.append(str1)
    return final_string


@app.route('/cluster', methods=['POST'])
def cluster():
    
    """Example file endpoint returning a prediction of iris
    ---
    parameters:
      - name: dataset
        in: formData
        type: file
        required: true
      - name: no_of_clusters
        in: formData
        type: number
        required: false
        
    responses:
        200:
            description: file to download
            schema:
                type: file

            
    """
    data = pd.read_excel(request.files['dataset'])
    
    unstructure = 'text'
    if 'col' in request.args:
        unstructure = request.form.get('col')
    no_of_clusters = 2
    print(request.form)
    if 'no_of_clusters' in request.form:
        no_of_clusters = int(request.form.get('no_of_clusters'))
        
    data = data.fillna('NULL')
    print(no_of_clusters)
    data['clean_data'] = cleantext(data[unstructure])
    count_vectorizer = CountVectorizer(analyzer='word',
                                 stop_words='english', min_df=10)
    counts = count_vectorizer.fit_transform(data['clean_data'])
    
    kmeans = KMeans(n_clusters=no_of_clusters)
    
    data['cluster_num'] = kmeans.fit_predict(counts)
    data = data.drop(['clean_data'], axis=1)
    
    
    # initiate an excel writer
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='Clusters', 
                  encoding='utf-8', index=False)
    
    
    # keep top words in another excel_sheet
    clusters = []
    for i in range(np.shape(kmeans.cluster_centers_)[0]):
        data_cluster = pd.concat([pd.Series(count_vectorizer.get_feature_names()),
                                  pd.DataFrame(kmeans.cluster_centers_[i])],
        axis=1)
        data_cluster.columns = ['keywords', 'weights']
        data_cluster = data_cluster.sort_values(by=['weights'], ascending=False)
        data_clust = data_cluster.head(n=10)['keywords'].tolist()
        clusters.append(data_clust)
    pd.DataFrame(clusters).to_excel(writer, sheet_name='Top_Keywords', encoding='utf-8')
    
    
    #Pivot of clusters
    data_pivot = data.groupby(['cluster_num'], as_index=False).size()
    data_pivot.name = 'size'
    data_pivot = data_pivot.reset_index()
    data_pivot.to_excel(writer, sheet_name='Cluster_Report', 
                  encoding='utf-8', index=False)
    
    
    # insert chart
    workbook = writer.book
    worksheet = writer.sheets['Cluster_Report']
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
            'values': '=Cluster_Report!$B$2:$B'+str(no_of_clusters+1)
            })
    worksheet.insert_chart('G2', chart)
    
    writer.save()
    
    
    # zipping files if you produce multiple excel output
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        names = ['cluster_output.xlsx'] # mention file names as an element if you have multiple sheets
        files = [output]
        for i in range(len(files)):
            data = zipfile.ZipInfo(names[i])
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, files[i].getvalue())
    memory_file.seek(0)
    response = make_response(send_file(memory_file, attachment_filename='cluster_output.zip',
                                       as_attachment=True))
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response
    

if __name__=='__main__':
    app.run(host='0.0.0.0')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


