# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: real
- Records: 240
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.525 | 0.9417 | 0.4167 |
| Avg attempts | 1 | 1.6167 | 0.6167 |
| Avg token estimate | 430.27 | 1044.53 | 614.26 |
| Avg latency (ms) | 3805.09 | 8769.46 | 4964.37 |

## Failure modes
```json
{
  "react": {
    "wrong_final_answer": 57,
    "none": 63
  },
  "reflexion": {
    "none": 113,
    "wrong_final_answer": 7
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
