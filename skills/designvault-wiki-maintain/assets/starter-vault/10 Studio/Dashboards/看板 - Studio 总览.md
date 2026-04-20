# 看板 - Studio 总览

- [[看板 - 最近完成]]
- [[看板 - 待我试玩]]
- [[看板 - 待决策]]
- [[看板 - 最近回写]]

```dataview
TABLE file.link AS 页面, status AS 状态, updated AS 更新
FROM "10 Studio/Execution Logs"
SORT updated DESC
LIMIT 8
```
