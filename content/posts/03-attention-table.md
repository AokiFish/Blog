---
slug: attention-from-scratch
title: 把注意力画成一张表：从零理解 Transformer
date: 2026-07-24 15:40:00
category: AI
tags: [AI, 深度学习, Transformer]
summary: 不推公式，只用一张 4×4 的表格和十几行 NumPy，把 self-attention 到底在算什么讲清楚。
cover: /static/img/cover-attention.svg
---

几乎所有 Transformer 的科普都会先给出那个公式：

```text
Attention(Q, K, V) = softmax(QKᵀ / √dk) · V
```

公式本身不复杂，但它掩盖了一个更直观的事实：**注意力就是加权平均，权重由「谁跟谁更像」决定**。

## 先从一个句子开始

假设输入是四个词：

```python
tokens = ["我", "在", "写", "代码"]
```

每个词先变成一个向量。为了能打印出来看，我们只用 3 维：

```python
import numpy as np

X = np.array([
    [1.0, 0.0, 0.2],   # 我
    [0.3, 0.8, 0.1],   # 在
    [0.1, 0.2, 0.9],   # 写
    [0.0, 0.9, 0.7],   # 代码
])
```

## 三步算出注意力

**第一步：算相似度。** 每个词都去和所有词（包括自己）做点积：

```python
scores = X @ X.T          # 4×4
```

得到的 `scores[i][j]` 就是第 i 个词「应该关注第 j 个词多少」的原始分数。

**第二步：归一化成权重。** 除以维度的平方根防止数值爆炸，再 softmax：

```python
d = X.shape[1]
weights = np.exp(scores / np.sqrt(d))
weights = weights / weights.sum(axis=1, keepdims=True)
```

**第三步：加权求和。** 用权重去混合所有词的信息：

```python
out = weights @ X         # 4×3
```

到这里，self-attention 就结束了。`out[0]` 不再是「我」这个词的原始向量，而是**混入了上下文之后的新表示**。

## 为什么除以 √d

假设 d = 512，每个分量方差是 1，那么点积的方差会累积到 512，标准差大约是 22。softmax 对大数值极其敏感——输入差 22 的话，输出几乎会退化成 one-hot，梯度全部消失。

除以 $\sqrt{d}$ 之后，方差重新回到 1 附近，softmax 才有温和的输出分布。

!!! note "一个可以自己验证的小实验"
    把上面代码里的 `/ np.sqrt(d)` 删掉，打印 `weights.max()`。当维度升到 64 以上时，你会看到某一列迅速趋近于 1，其余趋近于 0。

## 多头注意力在解决什么

单头注意力只有一个「相似度标准」。但语言里的关系是多维的：

| 头 | 可能学到的关系 |
| --- | --- |
| 头 1 | 代词指向哪个名词 |
| 头 2 | 动词和它的宾语 |
| 头 3 | 相邻词的局部搭配 |
| 头 4 | 句首与句尾的长距离依赖 |

多头注意力就是把向量切成 8 份（或更多），每一份各算各的注意力，最后拼回来。代价是参数量不变，但表达能力的上限高了很多。

## Q、K、V 到底是什么

回到公式里的三个字母，它们其实是同一个输入 X 经过三个不同线性变换的结果：

```python
W_q = np.random.randn(3, 3)
W_k = np.random.randn(3, 3)
W_v = np.random.randn(3, 3)

Q, K, V = X @ W_q, X @ W_k, X @ W_v
weights = softmax(Q @ K.T / np.sqrt(3))
out = weights @ V
```

- **Q（Query）**：我在找什么
- **K（Key）**：我能提供什么标签
- **V（Value）**：你选中我之后，真正拿走的内容

类比搜索引擎：Q 是你的搜索词，K 是网页标题，V 是网页正文。相似度决定排名，你最终读到的是正文。

理解了这层类比，剩下的编码器堆叠、位置编码、残差连接都是工程上的补丁，不再是认知负担。
