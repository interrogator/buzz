# depgrep: a language for searching linguistic dependencies

When bulding a search query with *buzzword*, you can select *Dependencies* to activate *depgrep* queries. *Depgrep* searches consist of combinations of *nodes* and *relations*, just like [Tgrep2](https://tedlab.mit.edu/~dr/Tgrep2/), on which this tool is based. Learning to create searches consists of learning:

1. How to specify nodes (including regular expressions)
2. How to specify relations between nodes
3. How to use bracketing, *OR* expressions, negation and wilcards

While Tgrep2's constituency search implementation supports macros, named nodes and so on, the structure of dependency grammars is such that most of these kinds of advanced features are generally not necessary. The three components above are enough to build complex queries. For example, the query:

```
F"nsubj" = x"PRON" <- (l/diagnos/ = X"VERB" -> (F"advmod" = w/correct|accurate|proper/))
```

Translates to:

```
Find pronouns who are the nominal subjects of the process *diagnose* or *misdiagnose*, if this process is modified by an adverb denoting correctness.
```

That is, match *she* in `She was accurately diagnosed with bipolar disorder by a doctor two years ago`.

Below is a guide for constructing such queries.

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
