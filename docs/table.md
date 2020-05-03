# From dataset to results

In buzz, datasets are not meant to be used for gaining insights into corpus data. Instead, Dataset is simply the contents of a loaded corpus or a search result, including all the entries you want, and all their attributes, even when some of these attributes are not important to you.

After you have the information you need within a Dataset, the next step is to transform it into data that you can more easily interpret, such as a table of frequencies, or keyness scores.

For this, you can use the `dataset.table()` method. It distills the total information of a dataset into something simpler. By default, this is a matrix of words by file:

```python
dtrt = Corpus('dtrt/do-the-right-thing-parsed').load()
dtrt.table().head().to_html()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>w</th>
      <th>.</th>
      <th>,</th>
      <th>the</th>
      <th>..</th>
      <th>you</th>
      <th>and</th>
      <th>i</th>
      <th>to</th>
      <th>a</th>
      <th>'s</th>
    </tr>
    <tr>
      <th>file</th>
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
      <th>01-we-love-radio-station-storefront</th>
      <td>17</td>
      <td>13</td>
      <td>16</td>
      <td>3</td>
      <td>0</td>
      <td>12</td>
      <td>4</td>
      <td>2</td>
      <td>6</td>
      <td>5</td>
    </tr>
    <tr>
      <th>02-da-mayor's-bedroom</th>
      <td>2</td>
      <td>3</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>03-jade's-apartment</th>
      <td>5</td>
      <td>4</td>
      <td>5</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>3</td>
    </tr>
    <tr>
      <th>04-jade's-bedroom</th>
      <td>15</td>
      <td>6</td>
      <td>3</td>
      <td>6</td>
      <td>1</td>
      <td>4</td>
      <td>4</td>
      <td>6</td>
      <td>3</td>
      <td>6</td>
    </tr>
    <tr>
      <th>05-sal's-famous-pizzeria</th>
      <td>16</td>
      <td>12</td>
      <td>14</td>
      <td>15</td>
      <td>4</td>
      <td>4</td>
      <td>6</td>
      <td>7</td>
      <td>7</td>
      <td>6</td>
    </tr>
    <tr>
      <th>06-mookie's-brownstone</th>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>07-street</th>
      <td>2</td>
      <td>1</td>
      <td>4</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>5</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>08-mother-sister's-stoop</th>
      <td>10</td>
      <td>7</td>
      <td>6</td>
      <td>4</td>
      <td>3</td>
      <td>0</td>
      <td>4</td>
      <td>3</td>
      <td>0</td>
      <td>3</td>
    </tr>
    <tr>
      <th>09-sal's-famous-pizzeria</th>
      <td>32</td>
      <td>17</td>
      <td>10</td>
      <td>23</td>
      <td>8</td>
      <td>6</td>
      <td>10</td>
      <td>4</td>
      <td>9</td>
      <td>7</td>
    </tr>
    <tr>
      <th>10-sal's-famous-pizzeria</th>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>

This is the most basic kind of table.

For more complex tables, you can use a number of keyword arguments:

| Keyword argument    | default           | type            | purpose |
| -- | -- | -- | -- |
| `show`                | `['w']`           | `list` of `str` | What token features to use as new columns. For example, `["w", "l"]` will show `word/lemma` |
| `subcorpora`          | `['file']`        | `list` of `str` | Dataset columns/index levels to use as new index. Same format as `show`. |
| `preserve_case`       |  `False`          |  `bool`         | Whether or not results should be lowercased before counting |
| `sort`                |  `"total"`        |  `str`          | Sort output columns by `"total"`/`"infreq"`, `"name"`/`"reverse"`. You can also pass in `"increase"`/`"decrease"` or `"static"`/`"turbulent"`, which will do linear regression and sort by slope |
| `relative`            |  `False`          |  `bool`/`Dataset` | Get relative frequencies. You can pass in a dataset to use as the reference corpus, or use `True` to use the current dataset as the reference (more info below) |
| `keyness`             |  `False`          |  `bool`/`"pd"`/`"ll"`  | Calculate keyness (percentage difference or log-likelihood) |
| `remove_above_p`      |  `False`          |  `bool`/`float`         | If `sort` triggered linear regression, `p` values were generated; you can pass in a float value, or `True` to use `0.05`. Results with higher `p` value will be dropped. |
| `multiindex_columns`  |  `False`          |  `bool`         | If `len(show) > 1`, make columns a pandas MultiIndex rather than slash-separated strings |
| `keep_stats`          |  `False`          |  `bool`         | If `sort` triggered linear regression, keep the associated stats in the table |
| `show_entities `      |  `False`          |  `bool`         | Display whole entity, rather than just matching tokens within entitiy |


## `show` and `subcorpora`

`show` and `subcorpora` can be used to customise exactly what your index and column values will be. The main features you will need can be accessed as per the following:

| Feature | Valid accessors |
|-------|------------------|
| file  | `file`            |
| sentence # | `s` | 
| word  | `w` |
| lemma | `l` |
| POS tag | `p` |
| wordclass | `x` |
| dependency label | `f` |
| governor index | `g` |
| speaker | `speaker` | 


So, `["l", "x", "speaker"]` will produce `lemma/wordclass/speaker`, which may look like `champion/noun/tony`. Any additional metadata in your corpus can also be accessed and displayed.

### Showing surrounding tokens

In addition to the regular `show` and `subcorpora` strings, you can use a special notation to get features from surrounding words: `+1w` will get the following word form; `-2l` will get the lemma form of the token two spaces back. Numbers 1-9 are accepted.

So, you could do `["-1x", "l", "x", "+1x"]` to show the preceding token's wordclass, matching lemma, matching wordclass, and following token's wordclass. This can be useful if you are interested in n-grams, group patterns, and the like.

## Multiindexing

When you have multiple items in `show`/`subcorpora`, by default, the index of the Table is a `pd.MultiIndex`, but the columns as slash-separated and kept as a single level.

If you want multiindex columns, you can turn them on with:

```python
multi = dtrt.table(show=['l', 'x'], multiiindex_columns=True)
```

If you wanted a slash-separated index, the easiest way is to use [pandas' transposer](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.transpose.html), `.T`:

```python
multi_row = dtrt.table(show=['file', 'speaker'], subcorpora=['w']).T
```

## Relative frequencies

Absolute frequencies can be difficult to interpret, especially when your subcorpora are different sizes. To normalise the frequencies, use the `relative` keyword argument.

`relative` keyword argument value can be:

| Value for *relative* | Interpretation |
| -- | -- |
| `False` | default: just use absolute frequencies |
| `True` | Calculate relative frequencies using the sum of the axis |
| `buzz.Dataset` | Turn dataset into a table using the same criteria used on the main table. Use the values of the result as the denominators | 
| `pd.Series` | Use the values in the `Series` as denominators |

For example, to find out the frequency of each noun in the corpus, relative to all nouns in the corpus, you can do:

```python
dtrt.just.wordclass.NOUN.table(relative=True)
```

And to find out the frequency of nouns, relative to all tokens in the corpus:

```python
dtrt.just.wordclass.NOUN.table(relative=dtrt)
```

So, the following two lines give the same output:

```python
dtrt.see.pos.by.speaker.relative().sort('total')
dtrt.table(show=['p'], subcorpora=['speaker'], relative=True, sort='total')
```
