# buzz: python corpus linguistics

<!--- Don't edit the version line below manually. Let bump2version do it for you. -->
> Version 1.0.3

> buzz is a linguistics tool for parsing and then exploring plain or metadata-rich text.

## Install

bash
```
pip install buzz
# or
git clone http://github.com/interrogator/buzz
cd buzz
python setup.py install
```

## Usage

First, make a folder (i.e. a corpus), which can contain either subfirectories or text files.

Text files should be plain text, but can have metadata stored in two ways. First, speaker names can be added by using capital letters and a colon, much like in a script. Second, you can use XML style metadata tags, preferably at the end of sentences and lines. Below demonstrates both:

`sopranos/s1/e01.txt`:

```
MELFI: My understanding from Dr. Cusamano, your family physician, is you collapsed? Possibly a panic attack? <metadata exposition=true, interrogative-type='intonation' move=info-request>
TONY: They said it was a panic attack <metadata emph-token=0, move='refute'>
MELFI: You don't agree that you had a panic attack? <metadata move='info-request', question=type='in'>
```

We can use buzz to model and parse this corpus.


```python
from buzz import Corpus
corpus = Corpus('sopranos')
parsed = corpus.parse()
# if you don't need constitency parses, you can speed things up with:
parsed = corpus.parse(cons_parser=None)
```

That will give us output in CONLL-U format, complete with original text, speaker names, all other metadata and constituency parses (if not excluded). It also creates another `Corpus` object, called `parsed` above, which we can exlore via commands like:

```python
parsed.files[0]
parsed.subcorpora.s1[:5]
```

You can interactively explore the corpus using the `tabview()` method:

```python
parsed.tabview()
```

The interactive view has a number of cool features, such as the ability to sort by row or column. Also, pressing `enter` on a given line will generate a concordance based on that line's contents. Neat!

You can use the `load()` method to load a whole or partial corpus into memory.

```python
loaded = parsed.load()
```

You don't explicitly need to do this, but it's great for small corpora. It creates a DataFrame-like object in memory, which means that operating on it is really fast. As a rule of thumb, datasets under a million words should be easily loadable on a personal computer.

If memory is a consideration, you can use a `usecols` keyword argument to limit what is loaded:

```python
loaded = parsed.load(usecols=['file', 's', 'i', 'w', 'l', 'speaker'])
```

This improves loading time, and increases the number of wods you can keep in memory. But, it also limits the kinds of searches that are possible. So, for the remainder of this `README`, we will assume our corpus is small, and this option was not necessary.

## Working with corpora

A corpus is a pandas DataFrame object. By default, the index is a multiindex, comprised of `filename`, `sent_id` and `token`. The columns are all the CONLL data, plus anything included as metadata:

```python
# show first five lines
loaded.head()
```

Because the object is based on DataFrame, expert users can directly use `pandas.DataFrame` operations if you know them:

```python
# get the 'word' column for the first five tokens
loaded.iloc[:5]['w']
```

You don't need to know pandas, however, in oter to use `buzz`, because `buzz` makes possible some more intuitive measures with linguisitcs in mind. For example, if you want to slice the corpus some way, you can easily do this using the `just` and `skip` properties:

```python
tony = loaded.just.speaker.TONY
# for regular expressions, like removing all punctuation:
no_punct = loaded.skip.xpos('PUNCT')
```

Any object created by `buzz` has a `.tabview()` method, which launches an interactive space where you can explore corpora, frequencies or concordances.

## spaCy

`spaCy` is used under the hood for dependency parsing, and a couple of other things. spaCy bring with it a lot of state of the art methods in NLP, such as language modelling and so on. You can access the `spaCy` representation of your data with:

```python
corpus.spacy()
# or
loaded.spacy()
```

## Searching

You can search a loaded or unloaded corpus with the `search` method.

Searches can be simple, simply looking over one column. Below, we look for any token with `nsubj` in the function column:


```python
nsubj = loaded.search('f', 'nsubj')
# or
nsubj = loaded.functions('nsubj')
# pandas equivalent, a little complex
nsubj = loaded[loaded['f'] == 'nsubj']
```

You can of course perform subsequent searches on the result object, drilling down to the data you're interested in. Metadata is searchable in the same way, so if you liked, you could cut down the results with:

```python
tony_nsubj = nsubj.search('speaker', 'TONY')
```

### Searching linguistic structures

If you need search constituencies or dependencies, `buzz` does that too. For constituencies, you can use the `tgrep` search language:

```python
trees = loaded.search('t', 'NP < JJ')
# or you can use the trees method
trees = loaded.trees('NP < JJ') 
```

For dependencies, you can use a modified version of `tgrep`, called `depgrep`, which makes a bit more sense for dependency data:

```python
deps = loaded.search('nsubj <- amond')
deps = loaded.deps('nsubj <- amond')
```

### Working with results

An important principle in `buzz` is the separation of searching and viewing results. You do not search for a concordance---instead, you search the corpus, and then visualise the output of the data as a concordance.

Concordancing is a nice way of looking at results. The main thing you have to do is tell `buzz` how you want the match column to look---it can be just the matching words, but also any combination of things. To show words and their parts of speech, you can do:

```python
nsubj.concordance(show=['w', 'p'])
```

You can also turn your data into frequency tables, which also requires a `subcorpora` argument, telling `buzz` what should be used as the rows (index) of the output. Below, we create a frequency table of `nsubj` tokens, in lemma form, organised by speaker.

```python
tab = nsubj.table(show='l', subcorpora=['speaker'])
```

This creates a `Frequencies` object, also based on DataFrame. You can use its `.tabview()` method to quickly explore results, sorting by columsn and so on. Pressing enter on a given frequency will bring up a concordance of instances of this entry.

### Plotting results

You can also use `buzz` to create high-quality visualisations of frequency data.

```python
tab.plot()
```