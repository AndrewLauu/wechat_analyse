-- 新建简化表
CREATE TABLE formatMsg
AS SELECT
-- time|talker|content|type*/ ​​
datetime(subStr(cast(m.createTime as text), 1,10),'unixepoch', 'localtime') talkTime,
(case m.isSend when 1 then 'Fei' when 0 then 'Tong' end) talker,
m.content,
-- (case m.type when 1 then length(m.content) else null end) length
m.type
FROM message m
WHERE m.talker='tongdeweixin7926'
/* and m.type in (1, 3, 34,43,47)
m.type
​1:文本和表情；
​3:图片
​34:语音消息
42:公众号名片
​43:视频文件
​47:收藏的表情
48：分享位置
​49:分享的链接,网址等 
50:语音电话​
​10000:撤回消息​
-1879048186:位置共享
1048625：微信表情库的表情
16777265：外部分享
419430449：转账
436207665：红包

SELECT * FROM ​formatMsg ​
--分离​纯文字
CREATE TABLE textMsg
AS SELECT content,talker
FROM ​​formatMsg fm
WHERE fm.type​ = 1
*/

-- Select formatMsg
Select * FROM formatMsg