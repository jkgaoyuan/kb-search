from typing import List, Dict
import re


class SpellCorrector:
    """基于编辑距离的简单搜索纠错器"""

    def __init__(self, dictionary: List[str] = None):
        self.dictionary = set(dictionary or [])
        self.max_distance = 2

    def add_to_dictionary(self, words: List[str]):
        """向词典中添加词汇"""
        for word in words:
            self.dictionary.add(word.lower())

    def _edit_distance(self, s1: str, s2: str) -> int:
        """计算两个字符串的莱文斯坦编辑距离"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def correct(self, query: str) -> Dict:
        """对查询词进行纠错建议"""
        if not query or not query.strip():
            return {"original": query, "suggestions": [], "corrected": None}

        words = re.findall(r'[^\s\p{P}]+', query)
        suggestions = []
        corrected_words = []
        has_correction = False

        for word in words:
            word_lower = word.lower()
            if word_lower in self.dictionary or len(word_lower) <= 2:
                corrected_words.append(word)
                continue

            # 查找词典中编辑距离最小的词
            best_match = None
            best_distance = self.max_distance + 1

            for dict_word in self.dictionary:
                dist = self._edit_distance(word_lower, dict_word)
                if dist < best_distance and dist <= self.max_distance:
                    best_distance = dist
                    best_match = dict_word

            if best_match:
                suggestions.append({
                    "original": word,
                    "suggestion": best_match,
                    "distance": best_distance
                })
                # 保留原词的大小写风格（简单处理）
                if word[0].isupper():
                    best_match = best_match.capitalize()
                corrected_words.append(best_match)
                has_correction = True
            else:
                corrected_words.append(word)

        corrected_query = " ".join(corrected_words) if has_correction else None

        return {
            "original": query,
            "suggestions": suggestions,
            "corrected": corrected_query,
            "has_correction": has_correction
        }

    def suggest_similar(self, query: str, limit: int = 3) -> List[str]:
        """返回与查询词最相似的词典词汇"""
        if not query:
            return []

        query_lower = query.lower()
        candidates = []

        for dict_word in self.dictionary:
            dist = self._edit_distance(query_lower, dict_word)
            if dist <= self.max_distance and dict_word != query_lower:
                candidates.append((dist, dict_word))

        candidates.sort(key=lambda x: (x[0], x[1]))
        return [word for _, word in candidates[:limit]]
