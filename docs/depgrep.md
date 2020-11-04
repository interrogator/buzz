# depgrep: a language for searching linguistic dependencies

In addition to simple searches using `dataset.just` and `dataset.skip`, *buzz* supports complex querying of the dependency information produced during the parsing process. For a quick example, let's find nouns that are *taken* in *Do the Right Thing*:

```python
from buzz import Collection
corpus = Collection('do-the-right-thing').load()
taken = corpus.depgrep("x/NOUN/ <- l/take/")
taken.l.value_counts()[:3]
```

```
seat      4
shower    2
care      2
Name: l, dtype: int64
```

... *take a seat*, *take a shower*, *take care*. Makes sense. The advantage of this kind of searching is that you can find and count instances of the phrase, *take care*, even if what was actually said was *taking care*, *care was taken*, or *take only the greatest of care*. Let's concordance these to see exactly what we matched:

```python
taken.just.l(["seat", "shower", "care"]).conc()[["left", "match", "right", "speaker"]].to_html()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>left</th>
      <th>match</th>
      <th>right</th>
      <th>speaker</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ppressive heat . People are taking cold</td>
      <td>showers</td>
      <td>. Sticking faces in ice - cold , water</td>
      <td>stage_direction</td>
    </tr>
    <tr>
      <th>1</th>
      <td>ches ? I just come home to take a quick</td>
      <td>shower</td>
      <td>. Sal 's gon na be mad . Later for Sal</td>
      <td>MOOKIE</td>
    </tr>
    <tr>
      <th>2</th>
      <td>aid . Yeah , then ya should take better</td>
      <td>care</td>
      <td>of your responsibilities . What respons</td>
      <td>JADE</td>
    </tr>
    <tr>
      <th>3</th>
      <td>onsibilities ? I did n't stutter . Take</td>
      <td>care</td>
      <td>of your responsibilities . Y'know exact</td>
      <td>JADE</td>
    </tr>
    <tr>
      <th>4</th>
      <td>hade . No one says a word . Sal takes a</td>
      <td>seat</td>
      <td>at one of the tables . I 'm beat . Pino</td>
      <td>stage_direction</td>
    </tr>
    <tr>
      <th>5</th>
      <td>n na make up something special . Take a</td>
      <td>seat</td>
      <td>. There , that 's a clean table . Sal m</td>
      <td>SAL</td>
    </tr>
    <tr>
      <th>6</th>
      <td>hese ... I guess not . Da Mayor takes a</td>
      <td>seat</td>
      <td>on the stoop and puts the flowers to hi</td>
      <td>stage_direction</td>
    </tr>
    <tr>
      <th>7</th>
      <td>lla start to dance while Mookie takes a</td>
      <td>seat</td>
      <td>, the impartial observer that he is . W</td>
      <td>stage_direction</td>
    </tr>
  </tbody>
</table>

See how we matched something like *taking cold showers*? This wouldn't have turned up in a simple text search for *take a shower*.

## Dependency queries

`dataset.depgrep` can search for any combination of *nodes* and *relations*. Learning to create searches consists of learning:

1. How to specify nodes (including regular expressions)
2. How to specify relations between nodes
3. How to use bracketing, *OR* expressions, negation and wilcards

While [Tgrep2](https://tedlab.mit.edu/~dr/Tgrep2/) (a constituency searching language, on which depgrep is based) supports macros, named nodes and so on, the structure of dependency grammars is such that most of these kinds of advanced features are generally not necessary. The three components listed above are enough to build arbitrarily complex queries. For example, the query:

```
F"nsubj" = x"PRON" <- (l/diagnos/ = X"VERB" -> (F"advmod" = w/correct|accurate|proper/))
```

Translates to:

```
Find pronouns who are the nominal subjects of the process *diagnose* or *misdiagnose*, if this process is modified by an adverb denoting correctness.
```

That is, match *she* in `She was accurately diagnosed with bipolar disorder by a doctor two years ago`.

### Nodes

A node targets one token feature (word, lemma, POS, wordclass, dependency role, etc). It may be specified as a regular expression or a simple string match: `f/amod|nsubj/` will match tokens filling the *nsubj* or *amod* role; `l"be"` will match the lemma, *be*.

The first part of the node query chooses which token attribute is to be searched. It can be any of:

```
w : word
l : lemma
p : part of speech tag
x : wordclass / XPOS
f : dependency role
i : index in sentence
s : sentence number
```

If this character is provided in lowercase, your query will be case-insensitive. The following query matches words ending in *ing*, *ING*, *Ing*, etc:

```
w/(?i)ing$/
```

Use an uppercase `W` to specify a case-sensitive match.

The remainder of the query is the text to be matched for the specified feature. If you use quotation marks (e.g. `W"thing"`), the query will be a simple string match (for the word, *thing*). Using forward slashes indicates a [regular expression](https://www.regular-expressions.info/quickstart.html): `W/^th(i|o)ngs?$/` will match *thing*, *things*, *thong* or *thongs*.

### Relations

Relations specify the relationship between nodes. For example, we can use `f"nsubj" <- f"ROOT"` to locate nominal subjects governed by nodes in the role of *ROOT*. The thing you want to find is the leftmost node in the query. So, while the above query finds nominal subject tokens, you could use inverse relation, `f"ROOT" -> f"nsubj"` to return the ROOT tokens that govern a token in the *nsubj* role.

Available relations:

```
a = b   : a and b are the same node
a & b   : a and b are the same node (same as =)

a <- b  : a is a dependent of b
a <<- b : a is a descendent of b, with any distance in between
a <-: b : a is the only dependent of b
a <-N b : a is descendent of b by N generations

a -> b  : a is the governor of a
a ->> b : a is an ancestor of b, with any distance in between
a ->: b : a is the only governor of b (as is normal in many grammars)
a ->N b : a is ancestor of b by N generations

a + b   : a is immediately to the left of b
a +N b  : a is N places to the left of b
a <| b  : a is left of b, with any distance in between

a - b   : a is immediately to the right of b
a -N b  : a is n places to the right of b
a |> b  : a is right of b, with any distance in between

a $ b   : a and b share a governor (i.e. are sisters)

a $> b  : a is a sister of and to the right of b.
a $< b  : a is a sister of and to the left of b.

```

### Negation

Add `!` before any relation to negate it: `f"ROOT" != x"VERB"` will find non-verbal ROOT nodes.

### Brackets

Brackets can be used to make more complex queries:

```
f"amod" = l/^[abc]/ <- (f/nsubj/ != x/NOUN/)
```

The above translates to *match adjectival modifiers starting with a, b or c, which are governed by nominal subjects that are not nouns*

Note that **without** brackets, each relation/node refers to the leftmost node. In the following, the plural noun must be the same node as the *nsubj*, not the *ROOT*:

```
f"nsubj" <- f"ROOT" = p"NNS"
```

### *Or* expressions

You can use the pipe (`|`) to create an *OR* expression. To match nouns that are either governed by *ROOT*, or are plural, you can use:

```
x"NOUN" <- f"ROOT" | = p"NNS"
```

### Wildcards

You can use `__` or `*` to stand in for any token. To match any token that is the governor of a verb, do:

```
__ -> x"VERB"
```

## Running queries

To run a query, you simply use the `depgrep` method on a Corpus or `Dataset` (i.e., a parsed corpus in memory):

```python
corpus = Collection("do-the-right-thing").conllu.load()
query = 'F"nsubj"'  # match nominal subjects
corpus.depgrep(query)
```

Remember that you can use *depgrep* in combination with tools like `just` and `skip`. To get *nsubj* nodes spoken by Sal that aren't plural, you could do either of the following:

```python
corpus.just.speaker.SAL.depgrep('F"nsubj"').skip.pos.NNS
# or, with one query:
corpus.just.speaker.SAL.depgrep('f"nsubj != p"NNS"')
```

## Source?

Head over to [the *depgrep* GitHub repo](https://github.com/interrogator/depgrep) for the query language source code, and some more information.

## Where to next?

Next, perhaps you'd like to learn some more about [the use of *pandas*](pandas.md) within *buzz*?
