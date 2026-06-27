# Backend

1. How well did the sources pulled as context relate to the query?
2. Did the LLM manage to answer the full question - especially with the prompt including "If the answer is not in the context, say you don't know."
    - Example: "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
        - For this question, the LLM admitted to not being able to answer the whole question given the context provided for the first four queries due to the correct chunks not being pulled - this was solved by pulling context per company, reducing chunk size, and reranking. We now consistently get answers that completely answer the question provided