# AgentLens

**让 AI Agent 的每一次运行都变得可解释、可回放。**

AgentLens 是一个本地优先的 AI Agent 调试工具。它把一次黑盒 Agent 运行记录成可查看的时间线，让你清楚看到：调用了哪些模型、执行了哪些工具、每一步收到了什么输入、产生了什么输出、花了多长时间，以及究竟在哪里失败。

> GitHub 仓库名是 `agentlens`。当前 Python 包名仍然是 `sekibanki`，这是为了保持已有代码的导入方式不变。

## 它能解决什么问题？

普通日志通常只能告诉你“某一步出错了”。AgentLens 会把完整运行过程保存下来：

- 记录模型调用、工具调用、检索、规划和自定义步骤
- 支持嵌套步骤，展示 Agent 的真实执行结构
- 保存输入、输出、耗时、状态和异常 traceback
- 生成普通 JSON 文件，不绑定云服务，也不要求数据库
- 自带本地 Web 查看器，打开浏览器即可检查运行过程
- 不依赖特定 Agent 框架，任何 Python 项目都可以接入

## 30 秒运行起来

### 1. 安装

Windows PowerShell：

```powershell
git clone https://github.com/escape9th/agentlens.git
cd agentlens
python -m pip install -e .
```

macOS/Linux：

```bash
git clone https://github.com/escape9th/agentlens.git
cd agentlens
python -m pip install -e .
```

AgentLens 需要 Python 3.10 或更高版本。运行时只有 Python 标准库依赖。

### 2. 记录一次 Agent 运行

在你的 Agent 代码中加入 `TraceRecorder`：

```python
from sekibanki import TraceRecorder

with TraceRecorder("support-agent") as trace:
    with trace.span(
        "plan",
        input={"question": "我的订单 A-17 到哪里了？"},
    ) as plan:
        plan.set_output({"next": "lookup_order", "order_id": "A-17"})

    with trace.span(
        "lookup_order",
        kind="tool",
        input={"order_id": "A-17"},
    ) as tool:
        tool.set_output({"status": "shipped", "eta": "周五"})

    trace.log(
        "answer",
        output="订单 A-17 已发货，预计周五送达。",
    )

print(f"Trace 已保存到：{trace.path}")
```

默认情况下，trace 会保存到当前目录的 `.sekibanki/` 文件夹中。每一次运行对应一个 JSON 文件。

### 3. 打开查看器

在项目目录中运行：

```powershell
sekibanki serve
```

然后打开浏览器访问：

<http://127.0.0.1:8765>

你会看到：

- 左侧的运行记录列表
- 每次运行的完成/失败状态
- 总耗时和事件数量
- 按时间排列的 Agent 执行时间线
- 每一步的输入、输出、类型和耗时
- 失败步骤的错误信息

结束查看时，在终端按 `Ctrl+C`。

## 接入真实的模型和工具调用

AgentLens 不要求你更换模型 SDK 或 Agent 框架。只需要把想观察的操作放进 `span`：

```python
from sekibanki import TraceRecorder

with TraceRecorder(
    "research-agent",
    metadata={"environment": "local"},
) as trace:
    with trace.span(
        "call_model",
        kind="llm",
        input=messages,
    ) as model:
        response = client.responses.create(input=messages)
        model.set_output(response.output_text)
        model.set_metadata(model="gpt-4.1-mini")

    with trace.span(
        "search",
        kind="tool",
        input={"query": response.output_text},
    ) as search:
        search.set_output(search_docs(response.output_text))
```

`input`、`output` 和 metadata 可以使用字典、列表、字符串、数字等 JSON 可序列化数据。如果传入无法直接序列化的对象，AgentLens 会自动使用 `repr()` 保存，避免调试记录反过来导致程序失败。

## 失败时会发生什么？

如果一个 span 内部抛出异常，AgentLens 会：

1. 记录异常类型、错误消息和完整 traceback
2. 记录该步骤的耗时
3. 将该步骤和整次运行标记为 `failed`
4. 继续抛出原始异常，不改变你原来的错误处理逻辑

示例：

```python
with TraceRecorder("payment-agent") as trace:
    with trace.span("charge_card", kind="tool") as charge:
        result = payment_provider.charge(order_id)
        charge.set_output(result)
```

即使 `charge()` 失败，trace 仍然会写入 `.sekibanki/`，方便你在异常发生后回放现场。

## 命令行参数

```text
sekibanki serve [--directory .sekibanki] [--host 127.0.0.1] [--port 8765]
```

示例：

```powershell
# 查看另一个目录中的 trace
sekibanki serve --directory .\traces

# 使用其他端口
sekibanki serve --port 9000
```

默认只监听本机 `127.0.0.1`。除非你清楚自己在做什么，否则不要使用 `--host 0.0.0.0`，因为这可能让 trace 查看器被同一网络中的其他设备访问。

## 不安装也可以试用

克隆仓库后，可以直接运行示例：

```powershell
python examples\quickstart.py
python -m sekibanki serve
```

## 开发和测试

项目运行时不依赖第三方库。执行测试：

```powershell
python -m unittest discover -s tests -v
```

当前测试覆盖：

- 嵌套 span 的记录
- 输入、输出和 metadata 的保存
- 成功和失败状态
- 异常 traceback 的记录
- JSON 文件读取
- trace 按时间排序
- 本地 Web 查看器和 API

欢迎提交 Issue、改进文档、增加框架适配示例，或为 trace 格式提出兼容性建议。

## 项目结构

```text
agentlens/
├── sekibanki/          # Python 包和命令行工具
│   ├── model.py        # Trace / TraceEvent 数据模型
│   ├── recorder.py     # TraceRecorder 和 Span
│   ├── store.py        # JSON trace 读写
│   ├── server.py       # 本地 Web 查看器
│   └── cli.py          # sekibanki serve
├── examples/           # 可直接运行的示例
├── tests/              # 自动化测试
└── .github/workflows/  # GitHub Actions
```

## 设计原则

AgentLens 第一版只专注于一件事：**让一次 Agent 运行变得容易理解。**

它不会偷偷把你的输入和输出上传到云端，也不会要求你把 Agent 改写成某个框架的格式。trace 是普通 JSON，可以放进 Issue、作为 bug 报告附件，或由其他工具继续处理。

## English summary

AgentLens is a tiny, local-first tracing and replay viewer for AI agents. It records nested model calls, tool calls, inputs, outputs, timing, and failures as portable JSON files, then serves them through a dependency-free local web UI.

```python
from sekibanki import TraceRecorder

with TraceRecorder("my-agent") as trace:
    with trace.span("call_model", kind="llm", input={"prompt": "hello"}) as step:
        step.set_output("hi")
```

Run `sekibanki serve` and open <http://127.0.0.1:8765>.

## License

MIT License. See [LICENSE](LICENSE).
