from flask import Flask, request
#from transformers import ElectraTokenizerFast, ElectraForQuestionAnswering
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from torch import nn
import pandas
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
# tokenizer_qa = ElectraTokenizerFast.from_pretrained("google/electra-small-discriminator")
# model_qa = ElectraForQuestionAnswering.from_pretrained("google/electra-small-discriminator").cuda()
# model_qa.load_state_dict(torch.load('./fine_electra.pt'))
elec_model = './electra_load'
ko_elec_model = './kor_electra_load'

tokenizer_sum = AutoTokenizer.from_pretrained("models/tokenizer/")
model_sum = AutoModelForSeq2SeqLM.from_pretrained("models/model/").cuda()
encoder_max_length = 1024

def generate_summarize(text, num_beam=2, max_length=50):
    inputs = tokenizer_sum(text, truncation=True, max_length=encoder_max_length,
                       return_tensors='pt')
    inputs.to('cuda')
    input_ids = inputs['input_ids']
    outputs = model_sum.generate(input_ids, num_beams=num_beam, max_length=max_length)
    outputs_dir = tokenizer_sum.batch_decode(outputs, skip_special_tokens=True)
    outputs_dir = ''.join(s for s in outputs_dir)
    return outputs_dir

@app.route('/electra', methods = ['POST'])
def get_answer():
    question = request.args['question']
    context = request.args['paragraph']
    # inputs = tokenizer_qa.encode_plus(question, context, return_tensors='pt')
    # inputs.to('cuda')

    # outputs = model_qa(**inputs)
    # answer_start = torch.argmax(outputs[0])  # get the most likely beginning of answer with the argmax of the score
    # answer_end = torch.argmax(outputs[1]) + 1
    # answer = tokenizer_qa.convert_tokens_to_string(tokenizer_qa.convert_ids_to_tokens(inputs['input_ids'][0][answer_start:answer_end]))
    
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

# @app.route('/electra_korean', methods = ['POST'])
# def get_answer():
#     question = request.args['question']
#     context = request.args['paragraph']
    
#     nlp = pipeline('question-answering', model=ko_elec_model, tokenizer=ko_elec_model)

#     QA_inputs = {
#         'question' : question,
#         'context' : context
#     }
#     answer = nlp(QA_inputs)['answer']

#     if len(answer) > 10:
#         n_answer = generate_summarize(answer)
#         if len(n_answer) < len(answer) : answer = n_answer
#     return answer

# @app.route('/bible_qa', methods = ['POST'])
# def get_answer():
#     question = request.args['question']
    
#     bible_data = pandas.read_csv('./bible_data/bible_summary.csv', header=None)
#     bible_text = bible_data[3].tolist()[1:]
#     tfidf_vectorizer = TfidfVectorizer()
#     tfidf_matrix = tfidf_vectorizer.fit_transform(bible_text)

#     max_index = 0
#     cosine_similar = 0
#     for i in range(len(bible_text)-1):
#         temp_cos_similar = cosine_similarity(tfidf_matrix[i], tfidf_matrix[len(bible_text)-1])
#         if temp_cos_similar > cosine_similar:
#             max_index = i
#             cosine_similar = temp_cos_similar

#     context = bible_text[max_index]
#     nlp = pipeline('question-answering', model=elec_model, tokenizer=elec_model)

#     QA_inputs = {
#     'question' : question,
#     'context' : context
#     }
#     answer = nlp(QA_inputs)['answer']
#     return answer

if __name__ == "__main__":
    app.run(port="8082")