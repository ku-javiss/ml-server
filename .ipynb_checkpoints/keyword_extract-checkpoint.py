from transformers import DistilBertTokenizerFast
from transformers import DistilBertForTokenClassification
import torch
import numpy

id2tag = {0: 'B-service', 1: 'O', 2: 'I-object_name', 3: 'I-track', 4: 'I-artist', 5: 'I-service', 6: 'I-object_type', 7: 'I-music_item', 8: 'B-artist', 9: 'B-year', 10: 'I-sort', 11: 'B-genre', 12: 'I-playlist', 13: 'B-playlist', 14: 'I-album', 15: 'B-object_type', 16: 'B-album', 17: 'B-sort', 18: 'B-object_name', 19: 'B-track', 20: 'B-music_item', 21: 'I-genre'}
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-cased')
model = DistilBertForTokenClassification.from_pretrained('distilbert-base-cased', num_labels=22)
model.load_state_dict(torch.load('./keyword_load/keyword_model.pt'))
device = torch.device('cuda')
model.to(device)

class keyword_extractor:

    def __init__(self):
        pass

    def get_keyword(self, sequence):

        inputs = tokenizer(sequence, return_tensors = "pt").to(device)
        tokens = inputs.tokens()

        outputs = model(**inputs).logits
        predictions = torch.argmax(outputs, dim=2)

        keyword = ''
        keyword_start_pos = 0
        keyword_end_pos = 0
        id_tags = predictions[0].cpu().numpy().tolist()
        for i in range(len(tokens)):
            token = tokens[i]
            tag = id2tag[id_tags[i]]
            if tag != 'O':
                keyword_start_pos = i
                break
            
        for i in range(len(tokens)-1,0,-1):
            token = tokens[i]
            tag = id2tag[id_tags[i]]
            if token != '[SEP]':
                if tag != 'O':
                    keyword_end_pos = i
                    break

        for i in range(keyword_start_pos,keyword_end_pos+1):
            if i == keyword_start_pos:
                keyword = tokens[i]
            else:
                if '##' in tokens[i]:
                    token = tokens[i].replace('##','')
                    keyword += token
                else:
                    token = ' ' + tokens[i]
                    keyword += token
        return keyword

