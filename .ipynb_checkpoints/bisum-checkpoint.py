from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("models/tokenizer/")
model = AutoModelForSeq2SeqLM.from_pretrained("models/model/")
encoder_max_length = 1024


def generate_summarize(text, num_beam=2, max_length=50):
    inputs = tokenizer(text, padding='max_length', truncation=True, max_length=encoder_max_length,
                       return_tensors='pt')
    input_ids = inputs.input_ids.to(model.device)
    attention_mask = inputs.attention_mask.to(model.device)
    outputs = model.generate(input_ids, attention_mask=attention_mask, num_beams=num_beam, max_length=max_length)
    outputs_dir = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    outputs_dir = ''.join(s for s in outputs_dir)
    return outputs_dir

