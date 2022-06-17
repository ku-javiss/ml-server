
from flask import Flask, request
import torch
from torch import nn
import pandas
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import domain_classifier as dc
import keyword_extract as ke
import crawler as cr
import bigbird_bible as bbb
import re

app = Flask(__name__)
elec_model = './electra_load'

tokenizer_sum = AutoTokenizer.from_pretrained("models/tokenizer/")
model_sum = AutoModelForSeq2SeqLM.from_pretrained("models/model/").cuda()
encoder_max_length = 1024

def check_news(question):
    front = '([tT]he |[oO]n |[aA][nN]* )'
    middle = '([aA][rR][tT][iI][cC][lL][eE][sS]*|[nN][eE][wW][sS]|[Jj][oO][uU][rR][nN][aA][lL])'
    back = '( [aA]bout| [oO]f)'
    pattern = '(' + front + '+' + middle + back + '*' + ')|(' + front + '*' + middle + back + '+' + ')'
    p = re.compile(pattern)
    if p.search(question) is None: return False
    return True

def generate_summarize(text, num_beam=2, max_length=50):
    inputs = tokenizer_sum(text, truncation=True, max_length=encoder_max_length,
                       return_tensors='pt')
    inputs.to('cuda')
    input_ids = inputs['input_ids']
    outputs = model_sum.generate(input_ids, num_beams=num_beam, max_length=max_length)
    outputs_dir = tokenizer_sum.batch_decode(outputs, skip_special_tokens=True)
    outputs_dir = ''.join(s for s in outputs_dir)
    torch.cuda.empty_cache()
    return outputs_dir

@app.route('/electra', methods = ['POST'])
def get_general_qa_answer():
    question = request.args['question']
    context = request.args['paragraph']
    
    nlp = pipeline('question-answering', model=elec_model, tokenizer=elec_model)

    QA_inputs = {
        'question' : question,
        'context' : context
    }
    answer = nlp(QA_inputs)['answer']

    if len(answer) > 10:
        n_answer = generate_summarize(answer)
        if len(n_answer) < len(answer) : answer = n_answer
    return answer

@app.route('/domain_classifier', methods = ['POST'])
def get_domain():
    question = request.args['question']
    classifier = dc.domain_classifier()
    domain = ""
    if request.args['sdomain'] in ["BibleQA", "GeneralQA", "News","PlayMedia"] :
        domain = request.args['sdomain']
    else:
        domain = classifier.test_sentences(question)

    url = ""
    news = {"site":"", "title":"", "content":""}
    news_set = {}
    for i in range(1, 6):
        input_news = news.copy()
        news_set[i] = input_news
    bible_answer = ""
    generals = ""
    bold = ""
    extractor = ke.keyword_extractor()
    crawler = cr.Crawler()
    bigbird = bbb.bigbird_bible() 

    if domain == "PlayMedia":
        keyword = extractor.get_keyword(question)
        url = crawler.startCrawl('youtube', keyword)
    elif domain == "BibleQA":
        bible_answer = bigbird.get_answer(question)
    else:
        if check_news(question) or domain == "News":
            keyword = extractor.get_keyword(question)
            crawled = crawler.startCrawl('news en', keyword, 10)
            for i in range(5):
                if len(crawled) <= i:
                    continue
                news_set[i+1]['site'] = crawled[i]['site']
                news_set[i+1]['title'] = crawled[i]['title']
                news_set[i+1]['content'] = generate_summarize(crawled[i]['content'])
            domain = "News"
        else:
            generals = crawler.startCrawl('google search',question)
            if len(generals[0]) == 1:
                generals = generals[0][0]
            elif len(generals[0]) == 2:
                bold = generals[0][0]
                generals = generals[0][1]
            else:
                generals = "Can't find simple answer from Google"

    result = {"domain":domain, "url":url, "news":news_set, "bible":bible_answer, "general":generals, "bold":bold}
    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port="8082")