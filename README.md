# Read epub file and the summary of each page side by side

I hack together this project in an evening. Expect bugs!

## How to run

1. Clone this repository, then install the requirements with `poetry` (require python >= 3.10).

2. Export your OpenAI API key to your environment variable:

```bash
export OPENAI_API_KEY=your_key_goes_here
```

3. Then fire up the Streamlit app:

```bash
streamlit run app.py --server.address=localhost --server.port=8501 
```