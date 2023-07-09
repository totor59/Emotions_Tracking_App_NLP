import spacy
from sklearn.base import BaseEstimator, TransformerMixin


class TextProcessor(BaseEstimator):
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.personalized_stopwords = ['feel', 'feeling', 'feelings', 'like', 'im', 'really', 'today', 'didnt', 'go', 'know', 'get', 'want', 'would', 'time', 'little', 'ive', 'still', 'even', 'one', 'people', 'think', 'bit', 'things', 'much', 'dont', 'make', 'day', 'something', 'back', 'going', 'way', 'could']

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        preprocessed_texts = []
        for text in X:
            doc = self.nlp(text)
            tokens = [token.lemma_ for token in doc]
            filtered_tokens = [token for token in tokens if not (self.nlp.vocab[token].is_punct or self.nlp.vocab[token].is_stop or len(token) < 3 or token.isnumeric() or token.isspace() or token.lower() in self.personalized_stopwords)]
            preprocessed_texts.append(' '.join(filtered_tokens))
        return preprocessed_texts
