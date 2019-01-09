# !/usr/bin/python
# -*- coding:utf-8 -*-

# import collections
import hashlib
import json
import re
import sqlite3
from datetime import datetime as dt

import emoji
import imageio
import jieba
import jieba.analyse
import matplotlib.pyplot as plt
import progressbar as p
from wordcloud import WordCloud as wc


def getPsw(imei, uid):
    key = str(imei) + str(uid)
    psw = hashlib.md5(key.encode()).hexdigest().lower()
    psw = psw[0:7]
    return psw  # 74ee691


def checkType():
    # Connect to SQL
    conn = sqlite3.connect('sqlcipher\\decrypted.db')
    c = conn.cursor()
    print('Connected to database.')

    # Check for unknown type
    typeList = [
        1, 3, 34, 42, 43, 47, 48, 49, 50, 10000, -1879048186, 1048625, 16777265, 419430449, 436207665
    ]
    c.execute(
        '''
        SELECT distinct type FROM message 
        WHERE talker="tongdeweixin7926" AND createTime<1550454552000
        '''
    )
    dbTypeList = [i[0] for i in c.fetchall()]

    if set(dbTypeList).issubset(set(typeList)):
        print('All type is known: ', ', '.join(str(i) for i in dbTypeList))
        formatDB(conn)
    else:
        print('Unknown type: ', set(dbTypeList) - set(typeList))
        conn.close()
        exit()
    return dbTypeList


def formatDB(connection):
    conn = connection
    # Connect to SQL
    # conn = sqlite3.connect('sqlcipher\\decrypted.db')
    c = conn.cursor()
    # print('Connected to database.')
    # Format message table
    c.execute('SELECT name FROM sqlite_master WHERE type="table"')
    isFormatted = [i[0] for i in c.fetchall()].count('formatMsg') == 1
    if isFormatted:
        c.execute('DROP TABLE formatMsg')
        print('Database has been formatted, dropped table `formatMsg`.')
    c.execute(
        '''
        CREATE TABLE formatMsg AS SELECT
        datetime(subStr(cast(m.createTime as text), 1, 10), 'unixepoch', 'localtime') talkTime,
        (case m.isSend when 1 then 'fei' when 0 then 'tong' end) talker,
        m.content,
        m.type
        FROM message m
        WHERE m.talker = 'tongdeweixin7926' AND createTime<1550540952000
        '''
    )
    conn.commit()
    print('Formatted database.')
    c.close()
    conn.close()
    print('Database disconnected.')


def analyse(dbTypeList):
    # Connect to SQL
    conn = sqlite3.connect('sqlcipher\\decrypted.db')
    c = conn.cursor()
    print('Connected to database.')

    # Message counting
    print('Processing types counting...')
    # typeDict = {
    #     1: '文本和表情',
    #     3: '图片',
    #     34: '语音消息',
    #     42: '公众号名片',
    #     43: '视频文件',
    #     47: '收藏的表情',
    #     1048625: '收藏的表情',
    #     48: '分享位置',
    #     49: '分享的链接,网址,小程序等',
    #     16777265: '分享的链接,网址等',
    #     50: 'video/voice电话',
    #     10000: '撤回消息',
    #     -1879048186: '位置共享',
    #     419430449: '转账',
    #     436207665: '红包'
    # }
    typeNumDict = {}
    topDict = {}
    countDict = {}
    tmpDict = {}  # Used to store tempVars in for-loop
    # typeList = [
    #     1, 3, 34, 42, 43, 47, 48, 49, 50, 10000, -1879048186, 1048625, 16777265, 419430449, 436207665
    # ]
    # c.execute('SELECT distinct type FROM message WHERE talker="tongdeweixin7926"')
    # dbTypeList = [i[0] for i in c.fetchall()]
    names = ['tong', 'fei', 'all']

    ## Type counting
    for i in dbTypeList:
        c.execute(f'SELECT COUNT(content) FROM formatMsg WHERE type={i}')
        typeNumDict[i] = c.fetchall()[0][0]
    typeNumDict[47] += typeNumDict[1048625]
    typeNumDict[49] += typeNumDict[16777265]
    typeNumDict.pop(1048625)
    del typeNumDict[16777265]
    typeNumDict['sum'] = sum(typeNumDict.values())
    countDict['TypeCount'] = typeNumDict
    print('Got type counting.')

    # Get text message
    # talkTime | talker | content | type
    print('Getting text type messages...')
    regEmoji = re.compile('\[.+?\]')
    regTB = re.compile(
        r'复制.+?看到【.+?】￥[\da-zA-Z]+?￥ .淘口令.|【.+】https://[\da-zA-Z./]+ 点击链接，.+?段描述￥[\da-zA-Z]+?￥后到.+?淘.+?\b|￥[\da-zA-Z]+?￥')
    # allText = tongText = feiText = ''
    for name in names:
        if name == 'all':
            ## Join text
            # textList = tmpDict['tongTextList'] + tmpDict['feiTextList']
            charNum = countDict['tongCharsNum'] + countDict['feiCharsNum']
            noTBText = tmpDict['tongText'] + '\n' + tmpDict['feiText']
        else:
            ## Select text
            c.execute(f"SELECT content FROM formatMsg WHERE talker='{name}' AND type=1")
            textList = [i[0] for i in c.fetchall()]
            text = ' '.join(textList)

            ## Longest text of original text
            maxText = max(textList, key=len)
            maxLen = wordCount(maxText).count()
            c.execute(
                f"""
                    SELECT talkTime FROM formatMsg
                    WHERE substr(content,1,10)='{maxText[:10]}'
                    AND talker='{name}'
                    """)
            maxTextDict = {
                'text': maxText,
                'len': maxLen,
                'time': c.fetchall()[0][0]
            }
            topDict[f'{name}MaxText'] = maxTextDict
            print(f"{name}'s longest text has {maxLen} words.")

            ## Remove taobao message => emoji stat
            noTBText = regTB.sub('', text)

        ## Storage
        with open(f'results\\{name}_text.txt', 'w', encoding='utf8') as f:
            f.write(noTBText)
        # locals()[f'{name}Text'] = text
        # tmpDict[f'{name}TextList'] = textList
        tmpDict[f'{name}Text'] = noTBText

        ## Remove [.+?] like WX emoji => count characters
        cleanText = regEmoji.sub('', noTBText)
        charNum = wordCount(cleanText).count()
        countDict[f'{name}CharsNum'] = charNum
        print(f"{name}'s {charNum} character-text-messages saved locally.")

        ## cleanText => generate wordCloud and get top1, top10..
        top1, top10 = genWordCloud(cleanText, name)
        topDict[f'{name}Top1'] = top1
        topDict[f'{name}Top10'] = top10

    ## Get joint text string
    # c.execute('SELECT content FROM formatMsg WHERE talker="tong" AND type=1')
    # tongTextList = [i[0] for i in c.fetchall()]
    # c.execute('SELECT content FROM formatMsg WHERE talker="fei" AND type=1')
    # feiTextList = [i[0] for i in c.fetchall()]
    # tongText = ' '.join(tongTextList)
    # feiText = ' '.join(feiTextList)

    ## Longest text
    # feiMaxText = max(feiTextList, key=len)
    # c.execute(
    #     f'''select talkTime from formatMsg
    #     where substr(content,1,5)={feiMaxText[:5]}
    #     and talker='fei'
    #     ''')
    # feiMaxTextDict = {
    #     'text': feiMaxText,
    #     'len': len(feiMaxText),
    #     'time': c.fetchall()[0][0]
    # }
    # topDict['feiText'] = feiMaxTextDict

    # tongMaxText = max(feiTextList, key=len)
    # c.execute(
    #     f'''select talkTime from formatMsg
    #     where substr(content,1,5)={tongMaxText[:5]}
    #     and talker="tong"
    #     ''')
    # tongMaxTextDict = {
    #     'text': tongMaxText,
    #     'len': len(tongMaxText),
    #     'time': c.fetchall()[0][0]
    # }
    # topDict['tongText'] = tongMaxTextDict

    ## Get and split emoji
    print('Splitting emoji...')
    tongText = tmpDict['tongText']
    feiText = tmpDict['feiText']
    allText = tmpDict['allText']

    ### List WeChat emoji
    emojiDict = {
        '': '😄',
        '': '😷',
        '': '😂',
        '': '😝',
        '': '😳',
        '': '😱',
        '': '😔',
        '': '😒',
        '': '👻',
        '': '🙏',
        '': '💪',
        '': '🎉',
        '': '🎁'
    }
    #### wechat messed emoji '' => '😄'. messed emoji, normal emoji
    for m, n in emojiDict.items():
        tongText = tongText.replace(m, n)
        feiText = feiText.replace(m, n)

    #### List normal emoji
    tongEmojiList = emoji.emoji_lis(tongText)
    feiEmojiList = emoji.emoji_lis(feiText)
    tongEmoji = [i['emoji'] for i in tongEmojiList]
    feiEmoji = [i['emoji'] for i in feiEmojiList]

    #### List wechat emoji
    tongEmojiList = regEmoji.findall(tongText)
    feiEmojiList = regEmoji.findall(feiText)

    ### Combine emoji+WX-emoji
    tongEmoji += tongEmojiList
    feiEmoji += feiEmojiList
    allEmoji = tongEmoji + feiEmoji

    # for name in ['tong', 'fei']:
    #     nameEmoji = name + 'Emoji'
    #     nameEmojiList = nameEmoji + 'List'
    #     nameText = name + 'Text'
    #     text = locals()[nameText]
    #     # Replace Weixin by [.+] like. emoji WXEmoji
    #     for e, w in emojiDict.items():
    #         locals()[nameText]=text.replace(e,w)
    #     # List emoji
    #     locals()[nameEmojiList] = regEmoji.findall(nameText)
    #     # Combine emoji+WX-emoji
    #     locals()[nameEmoji] += locals()[nameEmojiList]

    # tongTopEmoji, tongTopEmojiNum, tongEmojiDict = getTop(tongEmoji, 20)
    # feiTopEmoji, feiTopEmojiNum, feiEmojiDict = getTop(feiEmoji, 20)
    # allTopEmoji, allTopEmojiNum, allEmojiDict = getTop(allEmoji, 20)
    # tongEmojiNum = len(tongEmoji)
    # feiEmojiNum = len(feiEmoji)
    # allEmojiNum = tongEmojiNum + feiEmojiNum
    # countDict['tongEmoji'] = tongEmojiDict
    # countDict['feiEmoji'] = feiEmojiDict
    # countDict['allEmoji'] = allEmojiDict
    # print(
    #     f'''
    #     Tong's top emoji is {tongTopEmoji}, {tongTopEmojiNum} times in {tongEmojiNum},
    #     Fei's top emoji is {feiTopEmoji}, {feiTopEmojiNum} times in {feiEmojiNum},
    #     All top emoji is {allTopEmoji}, {allTopEmojiNum} times in {allEmojiNum}.
    #     '''
    # )

    ### Stat emoji
    for name in names:
        nameEmoji = locals()[f'{name}Emoji']
        topEmoji, topEmojiNum, emojiDict = getTop(nameEmoji, 20, isEmoji=True)
        emojiNum = len(nameEmoji)
        countDict[f'{name}EmojiNum'] = emojiNum
        topDict[f'{name}TopEmoji'] = {
            'emoji': topEmoji,
            'num': topEmojiNum,
            'Top20': emojiDict
        }
        print(f"{name}'s top emoji is {topEmoji}, {topEmojiNum} times in {emojiNum}")

    w = [
        p.Bar(left='|', marker='>', fill='-', right='|'),
        p.Percentage(), ' ',
        p.ETA()
    ]
    ### Voice length
    print('Processing voice length calculating...')
    c.execute('SELECT content FROM formatMsg WHERE type=34')
    voiceLen = [int(i[0].split(':')[1]) for i in c.fetchall()]
    voiceLen = sum(voiceLen) / 1000  # s
    countDict['voiceLength'] = voiceLen
    print(f'Total voice length {voiceLen} s.')

    ### Picture length
    print('Processing pictures length calculating...')
    c.execute('SELECT content FROM formatMsg WHERE type=3')
    picList = [i[0] for i in c.fetchall()]
    regHD = re.compile('(?<= hdlength=")\d+')
    regLen = re.compile('(?<= length=")\d+')  # space before 'length' to distinguish Len from HD and tempLen.
    picLen = 0
    # global w
    for pic in p.progressbar(picList, widgets=w, prefix='Pics '):
        HDLen = regHD.search(pic)
        Len = regLen.search(pic)
        # picLen += int(Len[0]) if HDLen is None or HDLen[0] == '0' else int(HDLen.[0])
        picLen += int(HDLen[0]) if HDLen and HDLen[0] != '0' else int(Len[0])
    countDict['picSize'] = picLen
    print(f'Total pictures length {picLen} KiB.')

    ### Transfer
    ### For isSend=0, transfer in: paysubtype=3; Transfer out: paysubtype=1
    ### isSend    subType     status
    ### 0         1           re
    ### 1         11          re - re
    ### 1         1           pay
    ### 0         11          re - pay

    ### 收到转账47.00元
    print('Processing transfer amount calculating...')
    c.execute("SELECT content FROM formatMsg WHERE type=419430449 AND talker='tong'")
    transList = [i[0] for i in c.fetchall()]
    transNum = len(transList)
    #### Amount
    transSum = 0
    regTrans = re.compile('(?<=收到转账)\d+\.\d+(?=元)')
    # global w
    for tr in p.progressbar(transList, widgets=w, prefix='Transfer '):
        transSum += float(regTrans.search(tr).group())
    # Method 2
    # transStr = " '.join(transList)
    # transList = regTrans.findall(transStr)
    # transSum = sum([int(i) for i in transList])
    countDict['transfer'] = {'Num': transNum, 'amount': transSum}
    print(f'Got {transNum} transactions sum at RMB {transSum}.')

    ### Reg Packet
    print('Processing red packet amount calculating...')
    c.execute('SELECT content FROM formatMsg WHERE type=436207665')
    redNum = len(c.fetchall())
    countDict['redPacketNum'] = redNum
    print(f'Got {redNum} red packets.')

    ## Date counting
    ### Get date list
    print('Processing date counting...')
    c.execute('SELECT talkTime FROM formatMsg WHERE talker="tong"')
    tongDateList = [dt.strptime(i[0], '%Y-%m-%d %H:%M:%S') for i in c.fetchall()]
    c.execute('SELECT talkTime FROM formatMsg WHERE talker="fei"')
    feiDateList = [dt.strptime(i[0], '%Y-%m-%d %H:%M:%S') for i in c.fetchall()]
    dateList = tongDateList + feiDateList

    ### Total number counting
    print('Processing messages counting...')
    # c.execute('SELECT COUNT(talkTime) FROM formatMsg')
    # dateNum = c.fetchall()[0][0]
    tongMsgNum = len(tongDateList)
    feiMsgNum = len(feiDateList)
    allMsgNum = tongMsgNum + feiMsgNum

    for name in names:
        n = locals()[f'{name}MsgNum']
        countDict[f'{name}MsgNumber'] = n
        print(f"Got {name}'s {n} messages.")

    ### Month counting
    # print('Processing messages counting...')
    monthList = [i.month for i in dateList]
    topMonth, topMonthNum, monthDict = getTop(monthList)
    topDict['topMonth'] = {
        'topTalkMonth': topMonth,
        'num': topMonthNum,
        'topDict': monthDict}
    print(f'Top1 month {topMonth} has {topMonthNum} messages.')

    ### Day counting AND total talking day number
    # print('Processing messages counting...')
    dayList = [f'{i.month}-{i.day}' for i in dateList]
    talkDayNum = len(set(dayList))
    topDay, topDayNum, dayDict = getTop(dayList, 30)
    topDict['day'] = {
        'topTalkDay': topDay,
        'num': topDayNum,
        'topDayDict': dayDict}
    countDict['TotalDays'] = talkDayNum
    print(f'Top1 day {topDay} of {talkDayNum} days has {topDayNum} messages.')

    ### Hour counting
    # print('Processing messages counting...')
    hourList = [i.hour for i in dateList]
    topHour, topHourNum, hourDict = getTop(hourList)
    topDict['hour'] = {
        'topTalkHour': topHour,
        'num': topHourNum,
        'topHourDict': hourDict}
    print(f'Top1 hour {topHour} has {topHourNum} messages.')

    #### Earliest 06:00-9:00 5 6 7 8 9
    #### TODO get date of early | late time.
    #### todo get individual e/l time and content
    #### IDEA time -> 2018.01.01+time -> util (cmp) -> readable -> readable-2018.01.01 -> time
    timeList = [
        i for i in dateList
        if i.hour in range(5, 10)
    ]
    earlyTime = min(timeList, key=lambda x: x.time())

    #### Latest 00:00-05:00 0 1 2 3 4
    timeList = [
        i for i in dateList
        if i.hour in range(5)
    ]
    lateTime = max(timeList, key=lambda x: x.time())
    topDict['earlyTime'] = earlyTime.strftime('%Y-%m-%d %H:%M:%S')
    topDict['lateTime'] = lateTime.strftime('%Y-%m-%d %H:%M:%S')
    print(f'Earliest is {earlyTime}, and latest is {lateTime}.')

    # conn.commit()
    c.close()
    conn.close()
    print('Database disconnected.')
    return {'top': topDict, 'count': countDict}


def getTop(myList, topK=None, isEmoji=False):
    w = [
        p.Bar(left='|', marker='>', fill='-', right='|'),
        p.Percentage(), ' ',
        p.ETA()
    ]
    myDict = {}
    # Item=month,hour
    # ItemNum=number of month, hour
    mySet = set(myList)
    myLen = len(mySet)
    for i in p.progressbar(mySet, widgets=w, prefix='Getting top '):
        myDict[i] = myList.count(i)
    if isEmoji:
        myTmpDict = {}
        for k, v in myDict.items():
            if not re.search('\[.*?\]', k):
                k += emoji.demojize(k, delimiters=('|', ''))
            myTmpDict[k] = v
        myDict = myTmpDict
    if not topK or topK > myLen:
        topK = myLen
    sortedSet = sorted(myDict.items(), key=lambda d: d[1], reverse=True)
    sortedDict = dict(sortedSet[:topK])
    # item count
    topItem, topItemNum = sortedSet[0]
    # Method 2
    # topItemNum = max(myDict.values())
    # topItem = [it for it, ct in myDict.items() if ct == topItemNum]
    return topItem, topItemNum, sortedDict


def genWordCloud(usr_text, usr):
    print(f"Start to generating {usr}'s wordcloud.")
    # Load dict stopwords.
    jieba.load_userdict('resources\\userdict.txt')
    jieba.analyse.set_stop_words('resources\\stopwords.txt')
    # Cut sentences and analyse.
    cut = jieba.cut(usr_text, HMM=True)  # didn't apply stopwords.
    txt = ' '.join(cut)
    print(f"{usr}'s cut segment has destroyed. Generating {usr}'s frequency dict...")
    cutFreq = jieba.analyse.extract_tags(txt, topK=300, withWeight=True)
    top10 = jieba.analyse.extract_tags(txt, topK=10)
    top1 = jieba.analyse.extract_tags(txt, topK=1)
    cutDict = dict(cutFreq)
    # todo frequent number
    # freq = collections.Counter()
    # for c in cut:
    #     freq[c] += 1
    # freq = dict(freq.most_common(50))
    # with open(f'{usr}_freq.txt', 'w') as f:
    #     f.write(str(freq))
    with open(f'results\\{usr}_cutdict.txt', 'w') as f:
        f.write(str(cutDict))

    # Generate wordcloud.
    print(f"Generating {usr}'s wordcloud...")
    colorMask = imageio.imread(f'resources\\mask_{usr}.png')
    wordcloud = wc(
        background_color='white',
        width=2000,
        height=2000,
        mask=colorMask,
        max_words=200,
        font_path='FZKATJW.TTF'
    )
    wordcloud = wordcloud.generate_from_frequencies(cutDict)
    print(f"Generated {usr}'s wordcloud.")
    # Show image.
    plt.imshow(wordcloud)
    plt.show()
    wordcloud.to_file(f'results\\{usr}_wordcloud.png')
    return top1, top10


def main():
    # func = input('''
    #     1: Calculate password;
    #     2: Analyse WeChat message.
    #     ''')
    func = '2'
    if func == '1':
        IMEI = input('IMEI: ')  # 794825438204445
        UID = input('UID: ')  # -1193869337
        password = getPsw(IMEI, UID)  # 74ee691
        print(password)
    elif func == '2':
        knownType = checkType()
        result = analyse(knownType)
        with open('results\\result.json', 'w', encoding='utf8') as j:
            json.dump(result, j, ensure_ascii=False)
        print('Result.json saved successfully.')
    else:
        print('Try again.')
        main()


class wordCount(object):
    """
    https://blog.csdn.net/lixiaowang_327/article/details/79151163
    先行空格分割，得到列表，再行处理列表中的每个元素
    例：Smart校服广告曲 => 6、Disrespectful Breakup => 2、打10086 => 2、hello啊hi => 3
    如果元素不包含中文，则该元素长度记为：1+数字个数
    如果元素不包含英文，则该元素长度记为：中文字符数+数字个数，可以直接使用len()方法
    如果元素同时包含中英文，则该元素长度记为：中文字符数+数字个数+1
    """

    # 初始化字符计数
    # charsNum = 0
    # ustring = ''

    def __init__(self, ustring):
        self.inputString = ustring

    def toHalf(self, fString):
        """
        字符串全角转半角
        :param fString: Full width string
        :return: Half width string
        """
        hString = ''
        for uchar in fString:
            inside_code = ord(uchar)
            # 全角空格直接转换
            if inside_code == 12288:
                inside_code = 32
            # 全角字符（除空格）根据关系转化
            elif 65281 <= inside_code <= 65374:
                inside_code -= 65248
            hString += chr(inside_code)
        return hString

    def simplify(self, s):
        """
        query预处理,保留中英文数字，全部转为小写
        :param s: Str
        :return: characters, letters and digit in s.
        """
        hStr = self.toHalf(s)
        s2 = re.sub(r'(?![\u4e00-\u9fa5]|[\da-zA-Z]).', ' ', hStr)
        s3 = re.sub(r'\s+', ' ', s2)
        return s3.strip().lower()

    # 判断是否包含中文
    def hasChinese(self, check_str):
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    # 判断是否包含英文
    # def hasEnglish(self, check_str):
    #     for ch in check_str:
    #         if u'a' <= ch <= u'z' or u'A' <= ch <= u'Z':
    #             return True
    #     return False

    def count(self):
        simpleStr = self.simplify(self.inputString)
        strList = simpleStr.strip().split(' ')  # 'hello world你好' => ['hello','world你好']
        charsNum = 0  # 初始化字符计数
        w = [
            p.Bar(left='|', marker='>', fill='-', right='|'),
            p.Percentage(), ' ',
            p.ETA()
        ]

        if len(strList) <= 0:
            raise ValueError('String is null')

        for string in p.progressbar(strList, widgets=w, prefix='Counting '):
            hasZH = self.hasChinese(string)

            # Count [.*?] like emoji and remove them.
            # Apple like emoji is regard as a character.
            emojiNum = len(re.findall('\[.+?\]', string))
            string = re.sub('\[.+?\]', '', string)
            charsNum += emojiNum

            # ZH only or mixed.
            if hasZH:
                enNum = len(re.findall('[a-zA-Z]+|\d+', string))
                charsNum += enNum
                # Remove English to leave Chinese characters only.
                string = re.sub(r'[a-zA-Z]+|\d+', '', string)
                charsNum += len(string)
            # 英文only
            else:
                charsNum += 1  # + len(string)
        return charsNum
        # return 0


if __name__ == '__main__':
    main()
