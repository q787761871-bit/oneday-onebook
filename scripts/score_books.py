#!/usr/bin/env python3
import json
import re
import sys

def score_book(book):
    name = book['name']
    author = book.get('author', '')
    source = book['source']
    oneliner = book.get('oneliner', '')
    
    # Strong veto - force ≤5
    veto_patterns = [
        r'教材', r'教程', r'导论', r'讲义', r'读本', r'指南', r'十五讲',
        r'通史', r'简史', r'入门', r'概论', r'原理', r'基础',
        r'心理学', r'经济学', r'生物学', r'物理学', r'化学'  # Intro textbooks
    ]
    
    for pattern in veto_patterns:
        if re.search(pattern, name):
            return {
                'name': name,
                'author': author,
                'score': 5,
                'reason': f'强否决: {pattern}类书籍',
                'subject_id': book['subject_id'],
                'pool': book['pool']
            }
    
    # Veto for pure literature/novels
    if 'tag:文学' in source or '小说' in name or '诗集' in name:
        return {
            'name': name,
            'author': author,
            'score': 5,
            'reason': '强否决: 文学类书籍',
            'subject_id': book['subject_id'],
            'pool': book['pool']
        }
    
    # Veto for biographies
    if '传记' in name or '回忆录' in name:
        return {
            'name': name,
            'author': author,
            'score': 5,
            'reason': '强否决: 传记/回忆录类',
            'subject_id': book['subject_id'],
            'pool': book['pool']
        }
    
    # Check for high-score indicators (named concepts, original theory)
    high_score_indicators = [
        r'利维坦', r'资本论', r'存在与时间', r'深描', r'ANT', r'行动者网络',
        r'惯习', r'场域', r'赤裸生命', r'欲望机器', r'知识型', r'规训',
        r'全景敞视', r'在世存在', r'共同体', r'虚无主义', r'实践感',
        r'象征交换', r'拟像', r'超真实', r'延异', r'解构', r'范式',
        r'不可通约性', r'证伪', r'科学革命', r'意识形态', r'异化',
        r'商品拜物教', r'逻各斯中心主义', r'他者', r'存在主义', r'结构主义',
        r'后结构主义', r'解构主义', r'女性主义', r'后现代', r'新教伦理',
        r'资本主义精神', r'学术与政治', r'合法性', r'克里斯玛',
        r'社会契约', r'公意', r'主权', r'分权', r'自然法', r'功利主义'
    ]
    
    for indicator in high_score_indicators:
        if re.search(indicator, name) or (oneliner and re.search(indicator, oneliner)):
            return {
                'name': name,
                'author': author,
                'score': 8,
                'reason': f'含原创概念: {indicator}',
                'subject_id': book['subject_id'],
                'pool': book['pool']
            }
    
    # Philosophy, political philosophy, sociology classics tend to be higher
    if 'tag:哲学' in source or 'tag:政治哲学' in source:
        return {
            'name': name,
            'author': author,
            'score': 7,
            'reason': '哲学/政治哲学类，有思想密度',
            'subject_id': book['subject_id'],
            'pool': book['pool']
        }
    
    if 'tag:社会学' in source or 'tag:人类学' in source:
        return {
            'name': name,
            'author': author,
            'score': 7,
            'reason': '社会学/人类学类，有田野/理论价值',
            'subject_id': book['subject_id'],
            'pool': book['pool']
        }
    
    if 'tag:历史' in source and ('文化史' in name or '观念史' in name or '思想史' in name):
        return {
            'name': name,
            'author': author,
            'score': 7,
            'reason': '观念史/思想史类，有学术价值',
            'subject_id': book['subject_id'],
            'pool': book['pool']
        }
    
    # Default: solid academic work, score 6
    return {
        'name': name,
        'author': author,
        'score': 6,
        'reason': '学术著作，无明显原创概念标记',
        'subject_id': book['subject_id'],
        'pool': book['pool']
    }

def main():
    all_scored = []
    for batch_num in range(3):
        with open(f'data/scoring-batch-{batch_num}.json') as f:
            books = json.load(f)
        
        for book in books:
            scored = score_book(book)
            all_scored.append(scored)
    
    # Filter score >= 7
    filtered = [b for b in all_scored if b['score'] >= 7]
    print(f'Total scored: {len(all_scored)}, >=7: {len(filtered)}')
    
    with open('data/scored-2026-06-03.json', 'w') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
