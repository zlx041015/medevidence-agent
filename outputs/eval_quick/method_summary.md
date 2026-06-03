# Method Comparison

| method_name | retrieval_recall_at_k | citation_precision | claim_consistency | hallucination_rate | human_review_trigger_rate |
| --- | --- | --- | --- | --- | --- |
| direct_llm | 0.0 | 0.0 | 0.0 | 1.0 | 0.8 |
| retrieve_then_summarize | 0.7 | 0.4 | 0.0 | 0.1 | 0.2 |
| workflow_with_rag_and_verifier | 0.5 | 0.2 | 0.0 | 0.1 | 0.8 |
