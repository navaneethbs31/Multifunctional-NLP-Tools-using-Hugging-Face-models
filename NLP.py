import streamlit as st
import torch
from transformers import (
    BartForConditionalGeneration,
    BartTokenizer,
    GPT2Tokenizer,
    GPT2LMHeadModel,
    pipeline,
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoModelForQuestionAnswering,
)

# Load models and tokenizers
# Summarization
model_name_summarization = "facebook/bart-large-cnn"
tokenizer_summarization = BartTokenizer.from_pretrained(model_name_summarization)
model_summarization = BartForConditionalGeneration.from_pretrained(model_name_summarization)

# Next word prediction
tokenizer_gpt2 = GPT2Tokenizer.from_pretrained('gpt2')
model_gpt2 = GPT2LMHeadModel.from_pretrained('gpt2')

# Text generation
tokenizer_gpt2_gen = GPT2Tokenizer.from_pretrained('gpt2')
model_gpt2_gen = GPT2LMHeadModel.from_pretrained('gpt2')

# Chatting model
model_name_chat = "microsoft/DialoGPT-medium"
tokenizer_chat = AutoTokenizer.from_pretrained(model_name_chat, padding_side='left')
model_chat = AutoModelForCausalLM.from_pretrained(model_name_chat)

# Sentiment analysis
sentiment_analysis = pipeline("sentiment-analysis")

# Question answering
model_name_qa = "bert-large-uncased-whole-word-masking-finetuned-squad"
tokenizer_qa = AutoTokenizer.from_pretrained(model_name_qa)
model_qa = AutoModelForQuestionAnswering.from_pretrained(model_name_qa)

# Streamlit app
st.title("Multifunctional NLP Tool")

# Summarization
st.header("Text Summarization")
text_to_summarize = st.text_area("Enter text for summarization:", height=150)
if st.button("Summarize"):
    inputs = tokenizer_summarization.encode("summarize: " + text_to_summarize, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model_summarization.generate(inputs, max_length=130, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer_summarization.decode(summary_ids[0], skip_special_tokens=True)
    st.subheader("Summary:")
    st.write(summary)

# Next word prediction
st.header("Next Word Prediction")
prompt_for_prediction = st.text_input("Enter a prompt for next word prediction:")
if st.button("Predict Next Word"):
    inputs = tokenizer_gpt2(prompt_for_prediction, return_tensors='pt')
    with torch.no_grad():
        outputs = model_gpt2(**inputs)
    next_token_logits = outputs.logits[:, -1, :]
    top_k_tokens = torch.topk(next_token_logits, 5).indices[0].tolist()
    predicted_tokens = [tokenizer_gpt2.decode([token]) for token in top_k_tokens]
    st.subheader("Predicted Next Words:")
    st.write(predicted_tokens)

# Text generation
st.header("Text Generation")
prompt_for_generation = st.text_input("Enter a prompt for text generation:")
if st.button("Generate Text"):
    generated = tokenizer_gpt2_gen.encode(prompt_for_generation, return_tensors='pt')
    if torch.cuda.is_available():
        model_gpt2_gen.to('cuda')
        generated = generated.to('cuda')
    with torch.no_grad():
        for _ in range(50):
            outputs = model_gpt2_gen(generated)
            next_token_logits = outputs.logits[:, -1, :]
            next_token = torch.multinomial(torch.softmax(next_token_logits, dim=-1), num_samples=1)
            generated = torch.cat((generated, next_token), dim=1)
            if next_token.item() == tokenizer_gpt2_gen.eos_token_id:
                break
    generated_text = tokenizer_gpt2_gen.decode(generated[0], skip_special_tokens=True)
    st.subheader("Generated Text:")
    st.write(generated_text)

# Chatting with model
st.header("Chat with the Model")
user_input = st.text_input("You: ")
chat_history_ids = None
if st.button("Send"):
    if user_input:
        new_user_input_ids = tokenizer_chat.encode(user_input + tokenizer_chat.eos_token, return_tensors='pt')
        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if chat_history_ids is not None else new_user_input_ids
        chat_history_ids = model_chat.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer_chat.eos_token_id)
        response = tokenizer_chat.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
        st.write(f"Bot: {response}")

# Sentiment Analysis
st.header("Sentiment Analysis")
text_for_sentiment = st.text_area("Enter text for sentiment analysis:", height=150)
if st.button("Analyze Sentiment"):
    results = sentiment_analysis(text_for_sentiment)
    for result in results:
        st.write(f"Sentiment: {result['label']}, Score: {result['score']:.4f}")

# Question Answering
st.header("Question Answering")
context = st.text_area("Enter context for question answering:", height=150)
question = st.text_input("Enter your question:")
if st.button("Get Answer"):
    inputs = tokenizer_qa.encode_plus(question, context, add_special_tokens=True, return_tensors="pt")
    input_ids = inputs["input_ids"].tolist()[0]
    outputs = model_qa(**inputs)
    answer_start = torch.argmax(outputs.start_logits)
    answer_end = torch.argmax(outputs.end_logits) + 1
    answer = tokenizer_qa.convert_tokens_to_string(tokenizer_qa.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
    st.subheader("Answer:")
    st.write(answer)
