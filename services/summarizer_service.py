from transformers import pipeline, AutoTokenizer

class HuggingFaceSummarizer:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.summarizer = pipeline("summarization", model=model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def chunk_text_by_tokens(self, text, max_tokens=900):
        tokens = self.tokenizer.encode(text)
        chunks = []
        i = 0
        while i < len(tokens):
            # Find the next chunk boundary at a space (word boundary) if possible
            end = min(i + max_tokens, len(tokens))
            # decode to text, then find last space before end, to avoid cutting words
            chunk_text = self.tokenizer.decode(tokens[i:end], skip_special_tokens=True)
            if end < len(tokens):
                # try to avoid splitting in the middle of a word
                last_space = chunk_text.rfind(' ')
                if last_space != -1 and last_space > 100:  # avoid tiny chunks
                    chunk_text = chunk_text[:last_space]
                    end = i + self.tokenizer.encode(chunk_text, add_special_tokens=False).__len__()
            chunks.append(chunk_text.strip())
            i = end
        return chunks

    def summarize_long_text(self, text: str, max_length=130, min_length=30, do_sample=False) -> str:
        chunks = self.chunk_text_by_tokens(text, max_tokens=900)
        summaries = []
        for chunk in chunks:
            print(len(chunk))
            summary = self.summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=do_sample)
            summaries.append(summary[0]['summary_text'])
        return ' '.join(summaries)

    def summarize(self, text: str, max_length=130, min_length=30, do_sample=False) -> str:
        # For compatibility, summarize() now delegates to summarize_long_text
        return self.summarize_long_text(text, max_length, min_length, do_sample)
