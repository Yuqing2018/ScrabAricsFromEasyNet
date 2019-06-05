vscode + python3.7

1、添加虚拟环境env
py -m venv env  

2、激活虚拟环境
.\env\Scripts\activate

3、安装必要的package
pip install -r requirements.txt

4、安装mysql 本人安装的是 mysql-8.0.16
修改mysql 配置文件：config.cfg 
db_name : root  #默认
db_password: 123456  # mysql root 的密码，自己设置的
db_host : 127.0.0.1  #本地访问地址
db_database : poem   # schema

5、新建schema poem
6、python create.py  #添加系统运行需要的 table
7、python run.py  

##九歌API使用说明
###九歌介绍

###接口整体说明

1. 第一次发送藏头诗关键词  https://jiuge.thunlp.cn/sendPoem Post方式
2. 检查古诗生成情况  https://jiuge.thunlp.cn/getPoem Post方式

###sendPoem

url: https://jiuge.thunlp.cn/sendPoem post方式

输入参数(json格式)：

```
{
    "type":"JueJu"
    "yan":"5"或者"7"
    "keyword":关键词list，不能超过4个。
    "user_id":每个人不同的id
}
```
其中 type参数不动，yan参数 为"5"或者"7",剩余两个为每个用户不同的东西。

返回数据的格式：
```
如果返回的为 "mgc"，表示 关键词无法生成古诗；
如果返回的为其他（必定为数字），表示 前面还有  X首古诗等待排队
```

###getPoem

url: https://jiuge.thunlp.cn/getPoem post方式

输入参数(json格式)：

```
{
    "type":"JueJu"
    "yan":"5"或者"7"
    "keyword":关键词list，不能超过4个。
    "user_id":每个人不同的id
}
```

其中 type参数不动，yan参数 为"5"或者"7",剩余两个为每个用户不同的东西，与 sendPoem 参数相同即可。

返回数据的格式（json格式）：

```
{
    "code":"0"（表示还在生成中）
    "content": 数字（表示前面还有X首诗等待）
}
或者
{
    "code":"1"
    "content": 数组（表示生成的古诗 ["第一句","第二句","第三句","第四句"]
}
```
