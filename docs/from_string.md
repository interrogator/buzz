If you have text as strings and want to work with it, the following are available:

```python
import os
from buzz import Corpus, Parser
```

## Store the string as a corpus and then parse it

```python
corpus_name = 'demo'
corpus = Corpus.from_string('First sentence. Second sentence.', save_as=corpus_name)
assert os.path.isdir(corpus_name)
loaded = corpus.parse().load()
```

## Parse string without saving to disk

```python
parser = Parser()
parser.run('Input text here')
```

## Parse string, saving to disk along the way:

```python
parser = Parser()
parsed = parser.run('Input text here', save_as='second_demo')
loaded = parsed.load()
```

## String corpus use-cases

The main reason you might need this functionality is if you want quickly score new, unparsed documents against an existing corpus:


```python
new_texts = ['This is a text that I want to compare to corpus.', 'This too.']
parser = Parser()
reference = Corpus('reference-parsed').load()
for text in new_texts:
    # you can also pass the raw string to `similarity`, but this might mean reloading the parser...
    parsed = parser.run(text, save_as=False)
    print(reference.similarity(parsed))
```
