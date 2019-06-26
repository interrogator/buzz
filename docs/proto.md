# Prototypicality and similarity

`buzz` contains tools that help judge the similarity of parsed documents using a TF-IDF metric, similar to how a search engine returns an ordered set of similar documents to some search query.


The following will return a multiindexed `pandas.Series` containing the sentence and its similarity to each language model (i.e. *bin*). The basic `proto` command is avaiable by dot syntax as:

```python
proto = dtrt.proto.speaker.by.lemmata
# proto is a Series with scores as values. for nicer display we do:
proto.reset_index().to_html(index=False)
```

`proto` begins by segmenting the corpus by the feature of interest (`speaker` in the case above) into bins. It then builds as TF-IDF model of each bin using `[TfidfVectorizer]`(https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)` from [*scikit-learn*](https://scikit-learn.org/stable/index.html). These are stored in memory alongside the corpus. Then, each sentence is scored against each model.

To customise results further, you can use the full bracketted expression, which gives you some extra options, and allows you to construct the language model using combinations of word features.

* `show` is a list of features to join together when constructing the language model.
* `only_correct` can be switched off, in order to see how every sentence compared to every model.
* `n_top_members` can remove infrequent members of the metadata field of interest. This can speed up the operation, remove junk, and prevent outliers from having a large effect. 
* `top` can be used to quickly filter just the `n` most similar sentences per bin., So, setting it to `1` will 

```python
model_format = ['l', 'x']  # model corpus as lemma/wordclass tuples, rather than words
proto = dtrt.proto.file(show=model_format, only_correct=True, n_top_members=5, top=1)
# make the data print a little nicer as html:
proto.reset_index().drop('l/x', axis=1).to_html(index=False)
```

If you've seen the film, you may find yourself thinking how these sentences seem quite typical for their respective speakers.

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>speaker</th>
      <th>file</th>
      <th>s</th>
      <th>text</th>
      <th>similarity</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>BUGGIN' OUT</td>
      <td>33-street</td>
      <td>18</td>
      <td>Not only did you knock me down, you stepped on my new white Air Jordans that I just bought and that's all you can say, "Excuse me?</td>
      <td>0.334317</td>
    </tr>
    <tr>
      <td>DA MAYOR</td>
      <td>66-street</td>
      <td>53</td>
      <td>You didn't have to hit your son; he's scared to death as it was.</td>
      <td>0.324264</td>
    </tr>
    <tr>
      <td>JADE</td>
      <td>68-sal's-famous-pizzeria</td>
      <td>23</td>
      <td>Mookie, you can hardly pay your rent and you're gonna tell me what to do.</td>
      <td>0.299531</td>
    </tr>
    <tr>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>69-control-booth</td>
      <td>1</td>
      <td>As the evening slowly falls upon us living here in Brooklyn, New York, this is ya Love Daddy rappin' to you.</td>
      <td>0.287197</td>
    </tr>
    <tr>
      <td>MOOKIE</td>
      <td>97-sal's-famous-pizzeria</td>
      <td>25</td>
      <td>I know I wants to get my money.</td>
      <td>0.255000</td>
    </tr>
    <tr>
      <td>MOTHER SISTER</td>
      <td>96-mother-sister's-bedroom</td>
      <td>10</td>
      <td>I didn't.</td>
      <td>0.294582</td>
    </tr>
    <tr>
      <td>PINO</td>
      <td>77-storeroom</td>
      <td>26</td>
      <td>He, them, they're not to be trusted.</td>
      <td>0.339005</td>
    </tr>
    <tr>
      <td>SAL</td>
      <td>71-sal's-famous-pizzeria</td>
      <td>3</td>
      <td>Mookie, I don't know what you're talking about, plus I don't want to hear it.</td>
      <td>0.288566</td>
    </tr>
    <tr>
      <td>TINA</td>
      <td>73-tina's-apartment</td>
      <td>26</td>
      <td>You think I'm gonna let you get some, put on your clothes, then run outta here and never see you again in who knows when?</td>
      <td>0.324863</td>
    </tr>
    <tr>
      <td>stage_direction</td>
      <td>92-street</td>
      <td>1</td>
      <td>Jade and Mother Sister try to hold on to a streetlamp as a gush of water hits them; their grips loosens, the water is too powerful, and they slide away down the block and Da Mayor runs after them.</td>
      <td>0.256906</td>
    </tr>
  </tbody>
</table>


## Choosing what gets modelled

Whenever you are trying to calculate prototypicality or similarity of text, you first need to ask yourself, *in which sense should the texts be similar?*. One trivial kind of similarity is sentence length. For this, you would group your data into bins, find the average sentence length, and compare this average to the length of some new text. Obviously such a method isn't exactly the bleeding edge of linguistics. Nonetheless, *buzz*/*pandas* can help you with this; see [the *pandas* section](pandas.md) of these docs for some pandas recipes.

You're probably much more interested in a more complex kind of text similarity, based on the grammar, the word choices, or both. For this kind of research question, first, consider whether you should remove or normalise anything in your corpus. If you don't think you care about punctuation, you might like to drop it with `loaded_corpus.skip.wordclass.PUNCT`. From there, you could also remove words you think are unimportant, or normalise tokens or lemmata as you wish.

After modifying the dataset, the next step is to think about what to use as the `show` argument, as this can have a big effect on prototypes and similarity. 

### Words and wordings

Think of language as a combination of lexis (words used) and grammar (how they are ordered), with things like part-of-speech resting in the middle:

> token -> normalised word -> lemma ->  wordclass -> part-of-speech -> dependency label

If you're trying to look at how the bins differ in word choice, use `show='w'` only. If you are interested in the grammatical differences between groups, you might like to try wordclasses, so that you are modelling patterns like `DETERMINER ADJECTIVE NOUN VERB DETERMINER NOUN` (instead of *the hungry cat ate the rat*). 

`show` can be a list, in which case multiple token features are used in the model. `show=['f', 'x']`, for example, would model the text by dependency labels and wordclasses. `I run` would become `nsubj/PRON root/VERB`. Among other effects, this would negate the influence of tense, showing no distinction between `run` and `ran`.