from transformers import BigBirdTokenizerFast, BigBirdForQuestionAnswering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import pandas
import re

tokenizer = BigBirdTokenizerFast.from_pretrained("abhinavkulkarni/bigbird-roberta-base-finetuned-squad")
model = BigBirdForQuestionAnswering.from_pretrained("abhinavkulkarni/bigbird-roberta-base-finetuned-squad")
model.load_state_dict(torch.load('./fine_bigbird.pt'))
device = torch.device('cuda')
model.to(device)

bible_data = pandas.read_csv('bible_summary.csv', header=None)
bible_book = bible_data[1].tolist()[1:]
bible_chapter = bible_data[2].tolist()[1:]

class bigbird_bible:

    def __init__(self):
        pass

    def get_answer(self, question):
        bible_text = bible_data[3].tolist()[1:]
        bible_book = bible_data[1].tolist()[1:]
        bible_chapter = bible_data[2].tolist()[1:]
        bible_text.append(question)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(bible_text)

        cosine_sims = []
        for i in range(len(bible_text)-1):
            temp_cos_similar = cosine_similarity(tfidf_matrix[i], tfidf_matrix[-1])
            cosine_sims.append([temp_cos_similar, i])
            
        cosine_sims.sort(reverse=True)

        chapters = []
        for i in range(20):
            chapters.append(cosine_sims[i][1])
        context = ""
        for i in range(len(chapters)):
            context += bible_text[chapters[i]]
        n = len(context)
        start = 0
        maxtorch = 0
        answer_start = 0
        answer_end = 0
        answer = ""
        book = ""
        chapter = ""
        flag = True
        index = 0
        while flag:
            index += 1
            end = start + 15000
            if end >= n:
                flag = False
                end = n-1
            while True:
                if context[end] == "." or context[end] == "?" or context[end] == "!":
                    break
                end -= 1
            inputs = tokenizer.encode_plus(question, context[start:end+1], truncation=True, return_tensors='pt')
            inputs.to('cuda')
            
            outputs = model(**inputs)
            even = (float(torch.max(outputs[0])) + float(torch.max(outputs[1]))) / 2
            print(even)
            if even > maxtorch:
                maxtorch = even
                answer_start = torch.argmax(outputs[0])  
                answer_end = torch.argmax(outputs[1]) + 1
                answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs['input_ids'][0][answer_start:answer_end]))
            
            start = end + 1
            if context[start] == " ":
                start += 1
        if answer == "":
            answer = "Cannot find answer"
        else:
            start_i = 0
            end_i = 0
            for i in range(1, 20):
                temp = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(answer_input['input_ids'][0][answer_start-i:answer_end]))
                if temp[0] == "." or temp[0] == "?" or temp[0] == "!":
                    break
                start_i = i

            for i in range(1, 20):
                temp = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(answer_input['input_ids'][0][answer_start:answer_end+i]))
                end_i = i
                if temp[-1] == "." or temp[-1] == "?" or temp[-1] == "!":
                    break
                
            answer_extended = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(answer_input['input_ids'][0][answer_start-start_i:answer_end+end_i]))
            words = answer_extended.split(" ")
            for i in range(len(words)):
                if "<unk>" in words[i]:
                    words[i] = "[\w\W]*"
                    
            answer_extended = " ".join(words)
            chapter_index = 0
            for i in range(len(chapters)):
                p = re.compile(answer_extended)
                if p.search(bible_text[chapters[i]]) is None:
                    continue
                else:
                    chapter_index = chapters[i]
                    break
            book = bible_book[chapter_index]
            chapter = bible_chapter[chapter_index]
        answer_set = {"answer":answer, "book":book, "chapter":chapter}
        return answer_set