# arxml-diff

对 AUTOSAR ARXML 做稳定、可读的结构差异比较。工具忽略缩进和纯文本空白，使用标签与 SHORT-NAME 生成路径，报告新增、删除和修改节点，适合配置评审和 CI。

使用：python arxml_diff.py examples/before.arxml examples/after.arxml。

ARXML 是机器生成的大 XML，普通文本 diff 会把缩进、命名空间和节点顺序噪声放大，真正的配置变化反而不易发现。这个工具给出确定性结构摘要，减少评审成本。

## 许可证

MIT
