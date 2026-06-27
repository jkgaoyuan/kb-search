import re


def strip_markdown(text: str) -> str:
    # 移除 Markdown 标记，提取纯文本
    # 标题
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 粗体/斜体
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
    # 代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 链接
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 图片
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    # 列表标记
    text = re.sub(r'^[\s]*[-*+][\s]+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.[\s]+', '', text, flags=re.MULTILINE)
    # 水平线
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # 多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_summary(text: str, max_length: int = 200) -> str:
    # 生成摘要，优先取前max_length字符，在句子边界截断
    if len(text) <= max_length:
        return text

    # 在max_length附近找句号、问号、感叹号
    truncated = text[:max_length]
    for punct in ['。', '？', '！', '. ', '? ', '! ']:
        pos = truncated.rfind(punct)
        if pos > max_length * 0.7:  # 至少保留70%
            return truncated[:pos + 1]

    # 找不到句子边界，找空格
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        return truncated[:last_space] + '...'

    return truncated + '...'


def highlight_keywords(text: str, keywords: list[str]) -> str:
    # 高亮关键词（用于搜索结果展示）
    if not keywords:
        return text

    # 转义正则特殊字符
    escaped = [re.escape(kw) for kw in keywords if kw]
    if not escaped:
        return text

    pattern = re.compile(f'({"|".join(escaped)})', re.IGNORECASE)
    return pattern.sub(r'<mark>\1</mark>', text)
