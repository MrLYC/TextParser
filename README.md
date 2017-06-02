# TextParser

## 语法

### 解析表达式

#### 全局

```
xpath_info = xpath://*[@id="container"]/p[@class="info"]/text()
css_selector_info = select:#container > p.info
regex_info = regex:<p.+?class\s*=\s*"info".*?>(.*?)</p>
```

#### 局部

```
info = xpath://*[@id="container"]/p[@class="info"]/text()
title = regex{info}:title:\s*(.*?)$
```



### 变量

### 字符串变量

```
somebody := Tom
greet := hello {somebody}
```

