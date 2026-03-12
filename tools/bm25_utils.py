#!/usr/bin/env python3
"""
BM25 语义搜索工具 - 纯标准库实现，零依赖。

分词策略：
- 中文字符级 bigram（"老板我是" → ["老板", "板我", "我是"]）
- 英文/数字按空格和标点切词
- 两者合并作为词袋
"""

import re
import math
from typing import List, Dict, Tuple


# BM25 参数
BM25_K1 = 1.5  # 词频饱和参数，越大词频权重越高
BM25_B = 0.75  # 文档长度归一化参数


def tokenize(text: str) -> List[str]:
    """
    混合分词：中文 bigram + 英文单词。
    示例：
      "老板我是神人" → ["老板", "板我", "我是", "是神", "神人"]
      "BM25 算法" → ["bm25", "算法"]
      "老板 bm25" → ["老板", "bm2", "m25", "bm25"]
    """
    tokens = []

    # 1. 提取英文/数字词（转小写）
    english_tokens = re.findall(r"[a-zA-Z0-9]+", text)
    tokens.extend(t.lower() for t in english_tokens)

    # 2. 中文字符提取 bigram
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    for i in range(len(chinese_chars)):
        tokens.append(chinese_chars[i])  # unigram
        if i + 1 < len(chinese_chars):
            tokens.append(chinese_chars[i] + chinese_chars[i + 1])  # bigram

    return tokens


class BM25:
    """BM25 检索器，纯标准库实现。"""

    def __init__(self, corpus: List[str]):
        """
        corpus: 文档文本列表
        """
        self.corpus = corpus
        self.n = len(corpus)
        self.tokenized = [tokenize(doc) for doc in corpus]
        self.avgdl = sum(len(t) for t in self.tokenized) / max(self.n, 1)

        # 构建倒排索引：term → {doc_id: count}
        self.inverted: Dict[str, Dict[int, int]] = {}
        for doc_id, tokens in enumerate(self.tokenized):
            for token in tokens:
                if token not in self.inverted:
                    self.inverted[token] = {}
                self.inverted[token][doc_id] = self.inverted[token].get(doc_id, 0) + 1

        # 文档频率
        self.df: Dict[str, int] = {
            term: len(docs) for term, docs in self.inverted.items()
        }

    def score(self, query_tokens: List[str], doc_id: int) -> float:
        """计算单文档的 BM25 分数。"""
        doc_len = len(self.tokenized[doc_id])
        score = 0.0
        for token in query_tokens:
            if token not in self.inverted:
                continue
            tf = self.inverted[token].get(doc_id, 0)
            if tf == 0:
                continue
            df = self.df[token]
            idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1)
            tf_norm = (tf * (BM25_K1 + 1)) / (
                tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avgdl)
            )
            score += idf * tf_norm
        return score

    def search(
        self, query: str, top_k: int = 5, threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        搜索，返回 [(doc_id, score), ...] 按分数降序。
        threshold: 最低分数过滤（0 表示不过滤）
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 只对包含至少一个 query token 的文档打分（效率优化）
        candidate_ids = set()
        for token in query_tokens:
            if token in self.inverted:
                candidate_ids.update(self.inverted[token].keys())

        scored = [
            (doc_id, self.score(query_tokens, doc_id)) for doc_id in candidate_ids
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        if threshold > 0:
            scored = [(doc_id, s) for doc_id, s in scored if s >= threshold]

        return scored[:top_k]
