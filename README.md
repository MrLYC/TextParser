# TextParser

## 配置格式

```yaml
items:
  title:
    value: //title/text()
    default: demo
    type: xpath
  info:
    value: div.info
    type: css-selector
  value:
    value: value:(.*?)
    type: regex
    input: info
  group:
    value: demo-value
    type: contant
  id:
    value: ${group}-${value}
    type: template
```

