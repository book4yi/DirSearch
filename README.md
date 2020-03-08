# DirSearch
DirSearch是一款探测网站路径的工具,批量扫描网站的路径(目录或文件名或Api)，快速发现目标薄弱点  
## 功能：
- 实现异步协程(asyncio + aiohttp)快速扫描目标
- 主要结合响应码和其他辅助因素判断网站路径存活概率
- 对扫描过程中发现的目录，可进行递归探测
- 对路径成功命中计数+1存入mysql数据库中，以后使用时按命中次数降序取出

## 依存关系：  
```
运行环境：python3.8
安装所需依赖库：pip install requirement.txt
```

## 用法：
>usage: python3 dirsearch.py --target [urls file] [-o] [Storage path]  
optional arguments:  
  -h,　--help　　　　　　show this help message and exit  
  -t　TARGET,　--target　TARGET  
  　　　　　　　　　　　　The path where the urls file is located  
  -o　OUTPUT,　--output　OUTPUT  
  　　　　　　　　　　　　The location of the results  
  -r,　--recursive　　　　Recursive scan  

## 举例：
对target.txt的url进行目录探测，对存在的目录进行递归扫描，结果存放在result下的baidu子目录中。
>python DirSearch.py -t c:\target.txt -o baidu -r

## 说明：
- 文件中的url要以http或https开头，否则默认以http协议进行访问  
- 要把数据字典提前写入mysql数据库中，字段名分别为dir_name，count,可自行更改
- 结果默认存放result文件夹中当中

## 脚本判断依据：
目标url拼接字典后，通过python自动化脚本，建立A、B、C共3个列表。  
- A类表示可正常访问存在的目录或接口  
- B类表示存在但不可访问的目录或接口  
- C类表示可能存在的目录或接口  

对拼接字典后的url-a进行访问获取到HTTP状态码a，同时拼接构造随机字符串，去访问一个不存在的url-b，获取到HTTP状态码b。  
1. 若状态码a为200:  
结合页面关键字是否存在'404'，'not found'，'error'等关键词，若有则表示url可能为状态码为200的404界面，把url放入C类，否则进行下一步判断  
访问url-b，根据状态码b及页面相似度判断：  
a. 若状态码b为200，判断页面相似度是否小于95%，若是则把url放入C类  
b. 若状态码b为404，把url放入A类  
2. 若状态码a为403：  
- 访问url-b，若状态码b在[200,404]，把url放入B类  
3. 若状态码a为30X：  
- 设置allow_redirects=True再去访问，获取状态码c  
a. 若状态码c为200，同上判断  
b. 若状态码c为403，同上判断  


