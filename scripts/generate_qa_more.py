# -*- coding: utf-8 -*-
"""추가 Q&A 다양화 (420개 목표 달성)"""

import json
import sys
import io
import os
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent

def main():
    from anthropic import Anthropic

    # API 키 로드
    with open(BASE_DIR / '.env', 'r') as f:
        for line in f:
            if line.startswith('ANTHROPIC_API_KEY='):
                api_key = line.split('=', 1)[1].strip()

    client = Anthropic(api_key=api_key)

    # Q&A 로드
    with open(BASE_DIR / 'aidata/qa_pairs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    qa_pairs = data['qa_pairs']
    print(f'현재: {len(qa_pairs)}개')

    # 아직 다양화 안된 Q&A 찾기
    original_qa = [q for q in qa_pairs if not q.get('is_diversified', False)]
    remaining = original_qa[50:80]  # 30개 더 다양화

    print(f'추가 다양화: {len(remaining)}개 x 3 = ~{len(remaining)*3}개')

    PROMPT = """기존 Q&A를 기반으로 같은 내용의 다른 질문 표현 3개를 생성하세요.

Q: {question}
A: {answer}

JSON만 출력:
[{{"question": "한국어 표현"}}, {{"question": "English question"}}, {{"question": "짧은 표현"}}]
"""

    new_qa = []
    for i, qa in enumerate(remaining):
        print(f'  [{i+1}/{len(remaining)}]', end=' ')
        try:
            resp = client.messages.create(
                model='claude-3-5-haiku-20241022',
                max_tokens=400,
                messages=[{'role': 'user', 'content': PROMPT.format(question=qa['question'], answer=qa['answer'])}]
            )
            text = resp.content[0].text
            if '```' in text:
                parts = text.split('```')
                text = parts[1].replace('json', '') if len(parts) > 1 else text
            items = json.loads(text.strip())
            for item in items:
                new_qa.append({
                    'question': item['question'],
                    'answer': qa['answer'],
                    'category': qa.get('category', ''),
                    'source_doc_id': qa.get('source_doc_id', ''),
                    'source_type': qa.get('source_type', ''),
                    'source_file': qa.get('source_file', ''),
                    'is_diversified': True
                })
            print(f'+{len(items)}')
        except Exception as e:
            print(f'x {e}')
        time.sleep(0.3)

    # 병합 및 저장
    qa_pairs.extend(new_qa)
    data['qa_pairs'] = qa_pairs
    data['total_qa_pairs'] = len(qa_pairs)

    with open(BASE_DIR / 'aidata/qa_pairs.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 최종: {len(qa_pairs)}개')

if __name__ == "__main__":
    main()
