# Method Comparison

| method_name | retrieval_recall_at_k | citation_precision | claim_consistency | hallucination_rate | human_review_trigger_rate |
| --- | --- | --- | --- | --- | --- |
| direct_llm | 0.0 | 0.0 | 0.0 | 1.0 | 0.667 |
| retrieve_then_summarize | 0.75 | 0.417 | 0.0 | 0.0 | 0.333 |
| current_workflow | 0.083 | 0.333 | 0.0 | 0.667 | 0.667 |
| workflow_with_rag_and_verifier | 0.667 | 0.333 | 0.0 | 0.0 | 0.667 |
