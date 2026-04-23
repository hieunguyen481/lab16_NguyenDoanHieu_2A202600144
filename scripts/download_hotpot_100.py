import json
from pathlib import Path
from datasets import load_dataset
import random

def main():
    print("Loading hotpot_qa from huggingface...")
    dataset = load_dataset("hotpot_qa", "fullwiki", split="validation")
    
    # Lọc ngẫu nhiên 100 câu
    random.seed(42)  # Cố định seed
    indices = random.sample(range(len(dataset)), 100)
    
    examples = []
    for idx in indices:
        item = dataset[idx]
        context_chunks = []
        for title, sentences in zip(item["context"]["title"], item["context"]["sentences"]):
            context_chunks.append({
                "title": title,
                "text": "".join(sentences)
            })
            
        examples.append({
            "qid": item["id"],
            "difficulty": item["level"],
            "question": item["question"],
            "gold_answer": item["answer"],
            "context": context_chunks
        })
        
    out_path = Path("data/hotpot_100.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(examples)} examples to {out_path}")

if __name__ == "__main__":
    main()
