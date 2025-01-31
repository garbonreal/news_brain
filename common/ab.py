import jieba.analyse
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import chardet
from bs4 import BeautifulSoup


def get_summary(url):
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    # 发送请求
    try:
        response = requests.get(url, headers=headers)
        # 解析HTML
        result = chardet.detect(response.content)
        print(result)
        if result['encoding'] != 'utf-8' and result['encoding'] != 'GB2312':
            return "摘要未解析成功"
        soup = BeautifulSoup(response.content.decode(result['encoding'], 'replace'), 'html.parser')
        texts = [text for text in soup.stripped_strings]
        # 获取所有文本
        # 拼接所有字数大于15的文本
        long_text = ''
        for text in texts:
            if len(text) > 20:
                long_text += text + ' '

        # 分词和提取关键词
        keywords = jieba.analyse.extract_tags(long_text, topK=50, withWeight=True, allowPOS=('n', 'ns', 'vn', 'v'))

        # 构建句子向量表示
        sentences = long_text.split('。')
        sentence_vectors = []
        for sentence in sentences:
            words = jieba.lcut(sentence)
            vector = np.zeros(len(keywords))
            for i, keyword in enumerate(keywords):
                if keyword[0] in words:
                    vector[i] = keyword[1]
            sentence_vectors.append(vector)

        # 计算句子相似度
        similarity_matrix = cosine_similarity(sentence_vectors)

        # 使用TextRank算法提取摘要
        scores = np.sum(similarity_matrix, axis=1)
        top_sentences = scores.argsort()[-3:][::-1]
        summary = ''
        for i in top_sentences:
            summary += sentences[i] + '。'

        # 输出摘要结果
        return summary

    except requests.exceptions.RequestException:
        return "网址未成功打开"
