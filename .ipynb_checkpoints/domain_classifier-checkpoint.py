from torch.nn.utils.rnn import pad_sequence
from tensorflow.keras.preprocessing.sequence import pad_sequences
import torch.nn.functional as F
import numpy as np
import torch
from transformers import BertTokenizer
from transformers import BertForSequenceClassification

device = torch.device('cuda')
label_dict = { 'bible': 0, 'PlayMusicOrVideo': 1 ,'NotPlayMusicOrVideo': 2}
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=len(label_dict), output_attentions=False, output_hidden_states=False).cuda()
model.load_state_dict(torch.load('./domain_load/finetuned_BERT_domain.model'))
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)

class domain_classifier:

    def __init__(self):
        pass

    def Bert_tokenizer(self, sent):
        bert_sent = '[CLS] ' + sent + ' [SEP]'
        tokenized_text = tokenizer.tokenize(bert_sent)
        embedding_tokens = []
        for text in tokenized_text:
            encoded_sent = tokenizer.convert_tokens_to_ids(text)
            embedding_tokens.append(encoded_sent)
        return embedding_tokens

    def pad_sentences(self, sent, max_len=256):
        embedding_sent = pad_sequences([sent], maxlen=256, dtype='long', truncating='post', padding='post')
        return embedding_sent

    def create_masks(self, sent):
        masks = []
        for token in sent:
            mask = [float(t>0) for t in token]
            masks.append(mask)
        return masks

    def convert_data(self, sent):
        tokenized_sent = self.Bert_tokenizer(sent)
        padded_sent = self.pad_sentences(tokenized_sent)
        masks_sent = self.create_masks(padded_sent)
        inputs = torch.tensor(padded_sent)
        masks = torch.tensor(masks_sent)
        return inputs, masks    

    def test_sentences(self, sent):
        model.eval()
        inputs, masks = self.convert_data(sent)
        b_input_ids = inputs.to(device)
        b_input_mask = masks.to(device)
        with torch.no_grad():
            outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask) 
        logits = F.softmax(outputs[0], dim=1)
        logits = logits.cpu().numpy()
        pred = np.argmax(logits)
        if pred == 0:
            result = "BibleQA"
        elif pred == 1:
            result = "PlayMedia"
        else:
            result = "GeneralQA"
        return result