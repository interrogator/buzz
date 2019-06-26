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
preprocessed = Corpus('path/to/corpus').load().no_punct()
```

## Recipe: finding character mentions

In *Do the right thing*, as in any film, characters refer to other characters by name. It's interesting to compare who is mentioned, how often, and whether or not mentions are proportional to the amount of lines the character has. Let's investigate this using buzz and pandas.

First, we load in our data, and pull out the speakers' names.

```python
from buzz.corpus import Corpus
from buzz.table import Table
from collections import Counter, defaultdict

dtrt = Corpus('do-the-right-thing-parsed').load()
unique_speakers = set(dtrt.speaker)
unique_speakers.remove('stage_direction')
```

```python
{'AHMAD',
 "BUGGIN' OUT",
 'CEE',
 'CHARLIE',
 'CLIFTON',
 'COCONUT SID',
 'CROWD',
 'DA MAYOR',
 'EDDIE',
 'ELLA',
 ...
```

```python
# here is the data structure we save our results to
results = defaultdict(Counter)

# use buzz to get any sentence containing any string from the character list
matches = dtrt.sentences().just.text(unique_speakers, case=False)

for index, match in dtrt.sentences().iterrows():
    if match.speaker == 'stage_direction':
        continue
    found = [s for s in unique_speakers if s.lower() in match.text.lower()]
    for f in found:
        results[match.speaker][f] += 1

results = Table(results).fillna(0).astype(int).sort('total')
print(results.iloc[:14,:7].to_html())
```

This leaves us with a nice matrix of mentions; from this view, we can quickly see which characters are typically related 
                                                                                                    
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
