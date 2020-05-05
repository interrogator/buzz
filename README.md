[![Build Status](https://travis-ci.org/interrogator/buzz.svg?branch=master)](https://travis-ci.org/interrogator/buzz)
[![codecov.io](https://codecov.io/gh/interrogator/buzz/branch/master/graph/badge.svg)](https://codecov.io/gh/interrogator/buzz)
[![readthedocs](https://readthedocs.org/projects/buzz/badge/?version=latest)](https://buzz.readthedocs.io/en/latest/)
[![PyPI version](https://badge.fury.io/py/buzz.svg)](https://badge.fury.io/py/buzz)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# buzz: python corpus linguistics

<!--- Don't edit the version line below manually. Let bump2version do it for you. -->
> Version 3.1.2

> *buzz* is a linguistics tool for parsing and then exploring plain or metadata-rich text. This README provides an overview of functionality. Visit the [full documentation](https://buzz.readthedocs.io/en/latest/) for a more complete user guide.

## Install

*buzz* requires Python 3.6 or higher. A virtual environment is recommended.

```bash
pip install buzz[word]
# or
git clone http://github.com/interrogator/buzz
cd buzz
python setup.py install
```

## Frontend: *buzzword*

*buzz* has an optional frontend, *buzzword*, for exploring parsed corpora. To use it, install:

```bash
pip install buzz[word]
```

Then, generate a workspace, `cd` into it, and start:

```bash
python -m buzzword.create workspace
cd workspace
python -m buzzword
```

More complete documentation is available [here](https://buzzword.readthedocs.io/en/latest/), as well from the main page of the app itself.

A URL will be printed, which can be used to access the app in your browser.

## Creating corpora

*buzz* models plain text, or [CONLL-U formatted](https://universaldependencies.org/format.html) files. The remainder of this guide will assume that you are have plain text data, and want to process and analyse it on the command line using *buzz*.

First, you need to make sure that your corpus is in a format and structure that *buzz* can work with. This simply means putting all your text files into a folder, and optionally within subfolders (representing subcorpora).

Text files should be plain text, with a `.txt` extension. Importantly though, they can be augmented with metadata, which can be stored in two ways. First, speaker names can be added by using capital letters and a colon, much like in a script. Second, you can use XML style metadata markup. Here is an example file, `sopranos/s1/e01.txt`:

```html
<meta aired="10.01.1999" />
MELFI: My understanding from Dr. Cusamano, your family physician, is you collapsed? Possibly a panic attack? <meta exposition=true interrogative-type="intonation" move="info-request">
TONY: <meta emph=true>They</meta> said it was a panic attack <meta move="refute" /> 
MELFI: You don't agree that you had a panic attack? <meta move="info-request" question=type="in" />
...
```

If you add a `meta` element at the start of the text file, it will be understood as file-level metadata. For sentence-specific metadata, the element should follow the sentence, ideally at the end of a line. Span- and token-level metadata should wrap the tokens you want to annotate. All metadata will be searchable later, so the more you can add, the more you can do with your corpus.

To load corpora as *buzz* objects:

```python
from buzz import Corpus

corpus = Corpus("sopranos")
```

You can also make virtual corpora from strings, optionally saving the corpus to disk.

```python
corpus = Corpus.from_string("Some sentences here.", save_as="corpusname")
```

## Parsing

buzz uses [`spaCy`](https://spacy.io/) to parse your text, saving the results as CONLL-U files to your hard drive. Parsing by default is only for dependencies, but constituency parsing can be added with a keyword argument:

```python
# only dependency parsing
parsed = corpus.parse()
# if you also want constituency parsing, using benepar
parsed = corpus.parse(cons_parser="benepar")
# if you want constituency parsing using bllip
parsed = corpus.parse(cons_parser="bblip")
```

You can also parse text strings, optionally passing in a name under which to save the corpus:

```python
from buzz import Parser
parser = Parser(cons_parser="benepar")
for text in list_of_texts:
    dataset = parser.run(text, save_as=False)
```

The main advantages of parsing with *buzz* are that:

* Parse results are stored as valid CONLL-U 2.0
* Metadata is respected, and transferred into the output files
* You can do constituency and dependency parsing at the same time (with parse trees being stored as CONLL-U metadata)

the `parse()` method returns another `Corpus` object, representing the newly created files. We can explore this corpus via commands like:

```python
parsed.subcorpora.s1.files.e01
parsed.files[0]
parsed.subcorpora.s1[:5]
parsed.subcorpora["s1"]
```

### Parse command

You can also parse corpora without entering a Python session by using the `parse` command:

```bash
parse --language en --cons-parser=benepar|bllip|none path/to/conll/files
# or 
python -m buzz.parse path/to/conll/files
```

Both commands will create `path/to/conll/files-parsed`, a folder containing CONLL-U files.

### Loading corpora into memory

You can use the `load()` method to load a whole or partial corpus into memory, as a Dataset object, which extends the [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).

```python
loaded = parsed.load()
```

You don't need to load corpora into memory to work on them, but it's great for small corpora. As a rule of thumb, datasets under a million words should be easily loadable on a personal computer.

The loaded corpus is a `Dataset` object, which is based on the pandas DataFrame. So, you can use pandas methods on it:


```python
loaded.head()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th>w</th>
      <th>l</th>
      <th>x</th>
      <th>p</th>
      <th>g</th>
      <th>f</th>
      <th>e</th>
      <th>aired</th>
      <th>emph</th>
      <th>ent_id</th>
      <th>ent_iob</th>
      <th>ent_type</th>
      <th>exposition</th>
      <th>interrogative_type</th>
      <th>move</th>
      <th>question</th>
      <th>sent_id</th>
      <th>sent_len</th>
      <th>speaker</th>
      <th>text</th>
      <th>_n</th>
    </tr>
    <tr>
      <th>file</th>
      <th>s</th>
      <th>i</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="5" valign="top">text</th>
      <th rowspan="5" valign="top">1</th>
      <th>1</th>
      <td>My</td>
      <td>-PRON-</td>
      <td>DET</td>
      <td>PRP$</td>
      <td>2</td>
      <td>poss</td>
      <td>_</td>
      <td>10.01.1999</td>
      <td>_</td>
      <td>2</td>
      <td>O</td>
      <td>_</td>
      <td>True</td>
      <td>intonation</td>
      <td>info-request</td>
      <td>_</td>
      <td>1</td>
      <td>14</td>
      <td>MELFI</td>
      <td>My understanding from Dr. Cusamano, your family physician, is you collapsed?</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>understanding</td>
      <td>understanding</td>
      <td>NOUN</td>
      <td>NN</td>
      <td>13</td>
      <td>nsubjpass</td>
      <td>_</td>
      <td>10.01.1999</td>
      <td>_</td>
      <td>2</td>
      <td>O</td>
      <td>_</td>
      <td>True</td>
      <td>intonation</td>
      <td>info-request</td>
      <td>_</td>
      <td>1</td>
      <td>14</td>
      <td>MELFI</td>
      <td>My understanding from Dr. Cusamano, your family physician, is you collapsed?</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <td>from</td>
      <td>from</td>
      <td>ADP</td>
      <td>IN</td>
      <td>2</td>
      <td>prep</td>
      <td>_</td>
      <td>10.01.1999</td>
      <td>_</td>
      <td>2</td>
      <td>O</td>
      <td>_</td>
      <td>True</td>
      <td>intonation</td>
      <td>info-request</td>
      <td>_</td>
      <td>1</td>
      <td>14</td>
      <td>MELFI</td>
      <td>My understanding from Dr. Cusamano, your family physician, is you collapsed?</td>
      <td>2</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Dr.</td>
      <td>Dr.</td>
      <td>PROPN</td>
      <td>NNP</td>
      <td>5</td>
      <td>compound</td>
      <td>_</td>
      <td>10.01.1999</td>
      <td>_</td>
      <td>2</td>
      <td>O</td>
      <td>_</td>
      <td>True</td>
      <td>intonation</td>
      <td>info-request</td>
      <td>_</td>
      <td>1</td>
      <td>14</td>
      <td>MELFI</td>
      <td>My understanding from Dr. Cusamano, your family physician, is you collapsed?</td>
      <td>3</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Cusamano</td>
      <td>Cusamano</td>
      <td>PROPN</td>
      <td>NNP</td>
      <td>3</td>
      <td>pobj</td>
      <td>_</td>
      <td>10.01.1999</td>
      <td>_</td>
      <td>3</td>
      <td>B</td>
      <td>PERSON</td>
      <td>True</td>
      <td>intonation</td>
      <td>info-request</td>
      <td>_</td>
      <td>1</td>
      <td>14</td>
      <td>MELFI</td>
      <td>My understanding from Dr. Cusamano, your family physician, is you collapsed?</td>
      <td>4</td>
    </tr>
  </tbody>
</table>

You can also interactively explore the corpus with [tabview](https://github.com/TabViewer/tabview) using the `view()` method:

```python
loaded.view()
```

The interactive view has a number of cool features, such as the ability to sort by row or column. Also, pressing `enter` on a given line will generate a concordance based on that line's contents. Neat!

## Exploring parsed and loaded corpora

A corpus is a pandas DataFrame object. The index is a multiindex, comprised of `filename`, `sent_id` and `token`. Each token in the corpus is therefore uniquely identifiable through this index. The columns for the loaded copus are all the CONLL columns, plus anything included as metadata.

```python
# get the first sentence using buzz.dataset.sent()
first = loaded.sent(0)
# using pandas syntax to get first 5 words
first.iloc[:5]["w"]
# join the wordclasses and words
print(" ".join(first.x.str.cat(first.w, sep="/")))
```

```
"DET/My NOUN/understanding ADP/from PROPN/Dr. PROPN/Cusamano PUNCT/, DET/your NOUN/family NOUN/physician PUNCT/, VERB/is PRON/you VERB/collapsed PUNCT/?
```

You don't need to know pandas, however, in order to use *buzz*, because *buzz* makes possible some more intuitive measures with linguistics in mind. For example, if you want to slice the corpus some way, you can easily do this using the `just` and `skip` properties, combined with the column/metadata feature you want to filter by:

```python
tony = loaded.just.speaker.TONY
# you can use brackets (i.e. for regular expressions):
no_punct = loaded.skip.lemmata("^[^a-zA-Z0-9]")
# or you can pass in a list/set/tuple:
end_in_s = loaded.just.pos(["NNS", "NNPS", "VBZ"])
```

Any object created by *buzz* has a `.view()` method, which launches a `tabview` interactive space where you can explore corpora, frequencies or concordances.

## spaCy

[`spaCy`](https://spacy.io/) is used under the hood for dependency parsing, and a couple of other things. spaCy bring with it a lot of state of the art methods in NLP. You can access the `spaCy` representation of your data with:

```python
corpus.to_spacy()
# or
loaded.to_spacy()
```

## Searching dependencies

To search the dependency graph generated by spaCy during parsing, you can use the *depgrep* method.


```python
# search dependencies for nominal subjects with definite articles
nsubj = loaded.depgrep('f/nsubj.*/ -> (w"the" & x"DET")')
```

The search language works by modelling nodes and the links between them. Specifying a node, like `f/nsubj/`, is done by specifying the feature you want to match (`f` for `function`), and a query inside slashes (for regular expressions) or inside quotation marks (for literal matches).

The arrow-like link specifies that the `nsubj` must govern the determiner. The `&` relation specifies that the two nodes are actually the same node. Brackets may be necessary to contain the query.

This language is based on `Tgrep2`, syntax, customised for dependencies. It is still a work in progress, but documentation should emerge [here](https://buzzword.readthedocs.io/en/latest/depgrep/), with repository [here](https://github.com/interrogator/depgrep).

## Drill-down

When you search a `Corpus` or `Dataset`, the result is simply another Dataset, representing a subset of the Corpus. Therefore, rather than trying to construct one query string that gets everything you want, it is often easier to perform multiple small searches:

```python
query = 'f/nsubj/ <- f/ROOT/'
tony_subjects = loaded.skip.wordclass.PUNCT.just.speaker.TONY.depgrep(query)
```

Note that for any searches that do not require traversal of the grammatical structure, you should use the `skip` and `just` methods. *tgrep* and *depgrep* only need to be used when your search involves the grammar, and not just token features.

## Searching constituency trees

This is deprecated right now, due to lack of use (combined with requiring a lot of special handling). Make an issue if you really need this functionality and we can consider bringing it back, probably via BLLIP or Benepar. If you're making corpora with constituency parses, please use `parse = (S ...)` as sentence-level metadata to encode the parse.

## Viewing search results

An important principle in *buzz* is the separation of searching and viewing results. Unlike many other tools, you do not search for a concordance---instead, you search the corpus, and then visualise the output of the data as a concordance.

### Concordancing

Concordancing is a nice way of looking at results. The main thing you have to do is tell *buzz* how you want the match column to look---it can be just the matching words, but also any combination of things. To show words and their parts of speech, you can do:

```python
nsubj = loaded.just.function.nsubj
nsubj.conc(show=["w", "p"])
```

### Frequency tables

You can turn your dataset into frequency tables, both before or after searching or filtering. Tabling takes a `show` argument similar to the `show` argument for concordancing, as well as an additional `subcorpora` argument. `show` represents the how the columns will be formatted, and `subcorpora` is used as the index. Below we create a frequency table of `nsubj` tokens, in lemma form, organised by speaker.

```python
tab = nsubj.table(show="l", subcorpora=["speaker"])
```

Possible keyword arguments for the `.table()` method are as follows:

| Argument           | Description                                                                                                                                                                                                                                                                                      | Default  |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `subcorpora`         | Feature(s) to use as the index of the table. Passing in a list of multiple features will create a multiindex                                                                                                                                                                                     | `['file']` |
| `show`               | Feature(s) to use as the columns of the table. Passing a list will join the features with slash, so `['w', 'p']` results in columns with names like `'friend/NN'`                                                                                                                                | `['w']`    |
| `sort`               | How to sort the results. 'total'/'infreq', 'increase/'decrease', 'static/turbulent', 'name'/'inverse'                                                                                                                                                                                            | `'total'`  |
| `relative`           | Use relative, rather than absolute frequencies with `True`. You can also pass in Series, DataFrame or buzz objects to calculate relative frequencies against the passed in data.                                                                                                                 | `False`    |
| `remove_above_p`     | Sorting by increase/decrease/static/turbulent calculates the slope of the frequencies across each subcorpus, and p-values where the null hypothesis is no slope. If you pass in a float, entries with p-values above this float are dropped from the results. Passing in `True` will use `0.05`. | `False`    |
| `keep_stats`         | If True, keep generated statistics related to the trajectory calculation                                                                                                                                                                                                                         | `False`    |
| `preserve_case`      | Keep the original case for `show` (column) values                                                                                                                                                                                                                                                | `False`    |
| `multiindex_columns` | When `show` is a list with multiple features, rather than joining `show` with slashes, build a multiindex                                                                                                                                                                                        | `False`    |


This creates a `Table` object, which is also based on DataFrame. You can use its `.view()` method to quickly explore results. Pressing enter on a given frequency will bring up a concordance of instances of this entry.

### Plotting

You can also use *buzz* to create high-quality visualisations of frequency data. This relies completely on [pandas' plotting method](https://pandas.pydata.org/pandas-docs/stable/user_guide/visualization.html). A `plot` method more tailored to language datasets is still in development.

```python
tab.plot(...)
```

## Contributing

If you find bugs, feel free to create an issue. The project is open-source, so pull requests are also welcome. Code style is [`black`](https://github.com/psf/black), and versioning is handled by [`bump2version`](https://github.com/c4urself/bump2version).
