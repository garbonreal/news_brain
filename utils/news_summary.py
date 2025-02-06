from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize


def init_summarization_model():
    # Download the punkt tokenizer for sentence splitting
    nltk.download("punkt_tab")
    
    # Load the BART model and tokenizer
    cache_dir = "ml_model/bart-large-cnn"
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn", cache_dir=cache_dir)
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn", cache_dir=cache_dir)
    
    return model, tokenizer


def chunk_sentences(text, max_chunk_size=800):
    """ Split the text by sentence to ensure that you do not truncate sentences """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(word_tokenize(sentence))

        if current_length + sentence_length > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def get_news_summary(text, model, tokenizer, method="chunk"):
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

    if method == "chunk":
        chunks = chunk_sentences(text)
        summaries = []
        for chunk in chunks:
            summary = summarizer(chunk, max_length=150, min_length=50, do_sample=False)[0]["summary_text"]
            summaries.append(summary)
    
    elif method == "sliding_window":
        words = word_tokenize(text)
        summaries = []
        chunk_size=800
        overlap=100

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            print(len(chunk))
            summary = summarizer(chunk, max_length=150, min_length=50, do_sample=False)
            summaries.append(summary[0]["summary_text"])

    return " ".join(summaries)


if __name__ == "__main__":
    path = "D:\\Personal_Experience\\news_brain\\data\\67a4f91c7aaa1dd2c5ace666.txt"

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
      
    model, tokenizer = init_summarization_model()  

    print(get_news_summary(text, model, tokenizer, method="sliding_window"))
