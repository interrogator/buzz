# Working with pandas

> *`buzz` keeps everything in DataFrame-like objects, so you can use the powerful pandas syntax whenever you like. This section demonstrates how you can use some of pandas' features directly to explore your data in new ways.* 

## Monkey-patching Datasets

Just as you can with pandas, you can also write your own methods, and monkey-patch them to the Dataset object:

```python
from buzz import Dataset

def no_punct(df):
    return df.skip.wordclass.PUNCT

Dataset.no_punct = no_punct
```

From that point on, you can quickly pre-process your corpus with:

```python
preprocessed = Collection('path/to/corpus').load().no_punct()
```

## Recipe: finding character mentions

In *Do the right thing*, as in any film, characters refer to other characters by name. It's interesting to compare who is mentioned, how often, and whether or not mentions are proportional to the amount of lines the character has. Something like that is made trivial by *buzz*.

First, we load in our dataset, and get the set of all speaker names:

```python
dtrt = Collection('do-the-right-thing').load()
unique_speakers = set(dtrt.speaker)
```

We can use this set of names as a search query on the corpus, returning all tokens that are names:

```python
# don't care about case, but match entire word, not just part of it
mentions = dtrt.just.word(unique_speakers, case=False, exact_match=True)
```

Then, we turn this into a table, remove the non-speaker entries, and relativise the frequencies:

```python
# show word (i.e. mentioned speaker) by mentioner
tab = mentions.table(show='w', subcorpora='speaker')
# remove things we don't care about
tab = tab.drop('stage_direction').drop('stage_direction', axis=1)
# make relative, then cut down to top
tab = tab.relative()
tab.iloc[:14,:7].to_html()
```

This leaves us with a nice matrix of mentions:
                                                                                                    
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th style="text-align: right;"></th>
      <th style="text-align: right;">MOOKIE</th>
      <th style="text-align: right;">SAL</th>
      <th style="text-align: right;">JADE</th>
      <th style="text-align: right;">BUGGIN' OUT</th>
      <th style="text-align: right;">PINO</th>
      <th style="text-align: right;">DA MAYOR</th>
      <th>VITO</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>CROWD</th>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
    </tr>
    <tr>
      <th>DA MAYOR</th>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">6</td>
      <td style="text-align: right;">0</td>
    </tr>
    <tr>
      <th>EDDIE</th>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">2</td>
      <td style="text-align: right;">2</td>
      <td style="text-align: right;">0</td>
    </tr>
    <tr>
      <th>MISTER SEÑOR LOVE DADDY</th>
      <td style="text-align: right;">2</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">1</td>
    </tr>
    <tr>
      <th>MOOKIE</th>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">15</td>
      <td style="text-align: right;">3</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">6</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">7</td>
    </tr>
    <tr>
      <th>MOTHER SISTER</th>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">2</td>
      <td style="text-align: right;">0</td>
    </tr>
    <tr>
      <th>PINO</th>
      <td style="text-align: right;">4</td>
      <td style="text-align: right;">3</td>
      <td style="text-align: right;">2</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">3</td>
    </tr>
    <tr>
      <th>RADIO RAHEEM</th>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
      <td style="text-align: right;">0</td>
    </tr>
    <tr>
      <th>SAL</th>
      <td style="text-align: right;">21</td>
      <td style="text-align: right;">5</td>
      <td style="text-align: right;">6</td>
      <td style="text-align: right;">12</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">1</td>
      <td style="text-align: right;">0</td>
    </tr>
  </tbody>
</table>

A more in-depth example of the use of *pandas* is available [here](density.md).