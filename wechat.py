# !/usr/bin/python
# -*- coding:gbk -*-
from wordcloud import WordCloud as wc
import jieba
import matplotlib.pyplot as plt
import hashlib

def password(imei,uid):
    key=str(imei)+str(uid)
    key=key.encode()
    psw=hashlib.md5(key).hexdigest().lower()
    psw=psw[0,7]
    return psw
strr=''
txt = jieba.cut(strr)
txt = " ".join(txt)
wordcloud = wc(
    background_color = "white",
    width = 1000,
    height = 1000,
    max_words = 200,
    font_path = r'E:\02.ttf'
)
wordcloud = wordcloud.generate(txt)
plt.imshow(wordcloud)
plt.show()

