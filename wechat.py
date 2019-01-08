# !/usr/bin/python
# -*- coding:gbk -*-

import hashlib

import imageio
import jieba
import jieba.analyse
import matplotlib.pyplot as plt
from wordcloud import WordCloud as wc
import json
import sqlite3

def password(imei, uid):
    key = str(imei) + str(uid)
    psw = hashlib.md5(key.encode()).hexdigest().lower()
    psw = psw[0:7]
    return psw  # 74ee691


def cloud():
    strr = ''
    jieba.load_userdict('userdict.txt')
    jieba.analyse.set_stop_words('stopwords.txt')
    cut = jieba.cut(strr, HMM=True)
    txt = " ".join(cut)
    cutFreq = jieba.analyse.extract_tags(txt, topK=300, withWeight=True)
    cutDict = dict(cutFreq)
    print("Generating frequency dict...")
    with open('cutdict.txt', 'w+') as f:
        f.write(str(cutDict))
        print("Generating wordcloud...")
        colorMask = imageio.imread('mask')  # TODO

    wordcloud = wc(
        background_color='white',
        width=2000,
        height=2000,
        mask=colorMask,
        max_words=200,
        font_path='FZKATJW.TTF'
    )
    wordcloud = wordcloud.generate_from_frequencies(cutDict)
    plt.imshow(wordcloud)
    plt.show()
    wordcloud.to_file('wordcloud.png')


if __name__ == '__main__':
    imei = input("IMEI: ")
    uid = input("UID: ")
    psw = password(imei, uid)
    print(psw)
