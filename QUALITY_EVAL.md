# Backend

1. How well did the sources pulled as context relate to the query?
2. Did the LLM manage to answer the full question - especially with the prompt including "If the answer is not in the context, say you don't know."
    - Example: "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
        - For this question, the LLM admitted to not being able to answer the whole question given the context provided for the first four queries due to the correct chunks not being pulled - this was solved by pulling context per company, reducing chunk size, and reranking. We now consistently get answers that completely answer the question provided

# Frontend

1. Does the information display nicely.
2. Is the user experience simple/easy to use?

# Overall Usage:
1. We should be able to get all information on a follow-up by providing summary from first prompt
    - Given example in [PROMPT_AND_DESIGN.md], we get most (if not all) necessary info from follow-up


# Future Design Improvements

- Faster loading and/or asynchronous response setup to allow for actual message updates while the LLM is processing
- Explore semantic chunking more - had initially done this route, but stopped because the corpus was large - sized-chunking could cause issues with tables in the corpus (cuts them off in the middle)
- Instead of creating ticker-to-company-name-and-alias translations beforehand and then regex matching based on this, match the prompt to available tickers with a second LLM call before retrieval
- Add more interactive UI elements