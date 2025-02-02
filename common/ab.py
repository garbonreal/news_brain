import jieba.analyse
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import chardet
from bs4 import BeautifulSoup


def get_summary(url):
    # set headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    # send request
    try:
        response = requests.get(url, headers=headers)
        # detect encoding
        result = chardet.detect(response.content)
        print(result)
        if result['encoding'] != 'utf-8' and result['encoding'] != 'GB2312':
            return "failed to get encoding"
        soup = BeautifulSoup(response.content.decode(result['encoding'], 'replace'), 'html.parser')
        texts = [text for text in soup.stripped_strings]
        # get all text whose length is greater than 15
        long_text = ''
        for text in texts:
            if len(text) > 20:
                long_text += text + ' '

        # split text into words and extract keywords
        keywords = jieba.analyse.extract_tags(long_text, topK=50, withWeight=True, allowPOS=('n', 'ns', 'vn', 'v'))

        # build sentence vectors
        sentences = long_text.split('。')
        sentence_vectors = []
        for sentence in sentences:
            words = jieba.lcut(sentence)
            vector = np.zeros(len(keywords))
            for i, keyword in enumerate(keywords):
                if keyword[0] in words:
                    vector[i] = keyword[1]
            sentence_vectors.append(vector)

        # calculate similarity
        similarity_matrix = cosine_similarity(sentence_vectors)

        # use textrank to get top 3 sentences
        scores = np.sum(similarity_matrix, axis=1)
        top_sentences = scores.argsort()[-3:][::-1]
        summary = ''
        for i in top_sentences:
            summary += sentences[i] + '。'

        return summary

    except Exception as e:
        return "failed to get response"
