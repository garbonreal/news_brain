import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
import torch


def init_sentiment_analysis():
    # FinBERT Sentiment Analysis
    # https://github.com/yya518/FinBERT
    # Load the BART model and tokenizer
    cache_dir = "data_processing/ml_model/finbert-tone"
    model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone", cache_dir=cache_dir)
    tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone", cache_dir=cache_dir)
    
    return model, tokenizer


def get_sentiment(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    scores = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().cpu().numpy()[0]

    #LABEL_0: neutral; LABEL_1: positive; LABEL_2: negative
    sentiment_labels = ["neutral", "positive", "negative"]
    finbert_sentiment = sentiment_labels[np.argmax(scores)]
    finbert_polarity = scores[np.argmax(scores)]  # Highest probability score

    return finbert_polarity, finbert_sentiment


if __name__ == "__main__":
    path = "D:\\Personal_Experience\\news_brain\\data\\67a4f91c7aaa1dd2c5ace666.txt"

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    model, tokenizer = init_sentiment_analysis()
    print(get_sentiment(text, model, tokenizer))