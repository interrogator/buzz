## Recipe: leical density

> *This section uses lexical density as a case study as we learn to use buzz and pandas to analyse our corpus. Rather than actually investigating lexical density in the corpus, our real aim here is to show how you can easily extend the functionality of **buzz** corpora to fit your needs.*

[Lexical density](https://en.wikipedia.org/wiki/Lexical_density) is a well-known measure of complexity of text. It's a very simple calculation, making it a good learning exercise.

You can define and calculate lexical density in a number of ways. In common to all definitions is the idea that a simple text should receive a low score, and a complex text should receive a high score. How exactly lexical density has been calculated historically depends on what kinds of annotations are available. For example, Halliday (correctly) argues that *number of clauses* is more important than *number of words* for calculating lexical density, but datasets with clause boundary annotation are quite rare, and few tools can automate clause boundary identification.

Complexity itself has many different definitions as well. Are formal written texts more complex than spoken texts, because they tend to use bigger words? Or are spoken texts more complex because they contain a lot of false starts and grammatical abnormalities?

So, rather than coding dozens of different lexical density calculators, *buzz* is designed in such a way that rolling your own calculator is super simple. In fact, calculating lexical density of each sentence in a corpus can be written in a single line of Python. Let's do it in a few lines though, so it's easier to read.

First, we load our corpus, and group it into sentences using [pandas' groupby method](
https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.groupby.html):

```python
corpus = Corpus('do-the-right-thing-parsed').load()
groups = corpus.groupby(['file', 's'])
```

pandas groupby objects have an awesome `apply` method, which takes a function as an argument. The function is applied to each group, and the results joined together at the end.

So, we write our function, which calculates the lexical density of a given sentence:


```python
def calculate_density(sent):
    """
    - Divide the number of 'open class'/'content words' by the length of the sentence
    - Multiply by 100 for readability, as is tradition
    """
    open_wordclasses = {'NOUN', 'ADJ', 'ADV', 'VERB'}
    # the `x` column stands for xpos, which is equivalent to wordclass
    return sum(sent.x.isin(open_wordclasses)) / len(sent) * 100
```

Now, all we need to do is apply this function to our groups, and add the result to the Dataset as 
a new column:

```python
corpus['density'] = groups.apply(calculate_density)
# get a few sentences and their density scores
corpus.sentences()[['text', 'density']].iloc[8:14].to_html()
# the promised one-liner: dtrt['density'] = dtrt.groupby(['file', 's']).apply(lambda sent: sum(sent.x.isin({'NOUN', 'ADJ', 'ADV', 'VERB'})) / len(sent))
```

<table border="1" class="dataframe">
  <thead>
    <tr>
      <th>file</th>
      <th>s</th>
      <th>speaker</th>
      <th>text</th>
      <th>density</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="6" valign="top">01-we-love-radio-station-storefront</th>
      <th>9</th>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>This is Mister Señor Love Daddy.</td>
      <td>14.29</td>
    </tr>
    <tr>
      <th>10</th>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>Your voice of choice.</td>
      <td>40.00</td>
    </tr>
    <tr>
      <th>11</th>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>The world's only twelve-hour strongman, here on WE LOVE radio, 108 FM.</td>
      <td>33.33</td>
    </tr>
    <tr>
      <th>12</th>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>The last on your dial, but the first in ya hearts, and that's the truth, Ruth!</td>
      <td>28.57</td>
    </tr>
    <tr>
      <th>13</th>
      <td>DIRECTION</td>
      <td>The CAMERA, which is STILL PULLING BACK, shows that Mister Señor Love Daddy is actually sitting in a storefront window.</td>
      <td>39.13</td>
    </tr>
    <tr>
      <th>14</th>
      <td>DIRECTION</td>
      <td>The control booth looks directly out onto the street.</td>
      <td>60.00</td>
    </tr>
  </tbody>
</table>

Looking at these results, you can see some good and some bad results. Sentence 13 is correctly calculated as being far more complex than sentence 9. However, short sentences such as #10 can have high scores, despite not being complex, simply due to the very small sample size.

So, if these results are not satisfactory, we could simply `groupby` a different feature of the data, where the groups are large enough to give more consistent results.

Perhaps the solution to such a problem is to calculate density for a larger unit. Let's try this, getting lexical density per speaker, rather than simply by sentence.

```python
average = calculate_density(corpus[corpus.speaker != 'stage_direction'])
groups = corpus.groupby('speaker')
speaker_density = groups.apply(calculate_density)
print(f'Lexical density for all speakers combined: {average}')
print(speaker_density.sort_values().to_frame().to_html())
```

> Lexical density for all speakers combined: 42.93264248704663

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th style="text-align: right;">speaker</th>
      <th style="text-align: right;">density</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th style="text-align: right;">MISTER SEÑOR LOVE DADDY</th>
      <td style="text-align: right;">36.42</td>
    </tr>
    <tr>
      <th style="text-align: right;">RADIO RAHEEM</th>
      <td style="text-align: right;">37.70</td>
    </tr>
    <tr>
      <th style="text-align: right;">BUGGIN' OUT</th>
      <td style="text-align: right;">41.62</td>
    </tr>
    <tr>
      <th style="text-align: right;">MOOKIE</th>
      <td style="text-align: right;">41.88</td>
    </tr>
    <tr>
      <th style="text-align: right;">VITO</th>
      <td style="text-align: right;">42.18</td>
    </tr>
    <tr>
      <th style="text-align: right;">PINO</th>
      <td style="text-align: right;">43.11</td>
    </tr>
    <tr>
      <th style="text-align: right;">SAL</th>
      <td style="text-align: right;">44.65</td>
    </tr>
    <tr>
      <th style="text-align: right;">DA MAYOR</th>
      <td style="text-align: right;">44.67</td>
    </tr>
  </tbody>
</table>

As texts get larger, the density scores appear to converge, as we'd expect. That's a good sign that everything is working correctly!

## Sky == limit

*pandas* is a massive module, with a lot to learn and master. However, as you can see in the above examples, you're limited only by your imagination when it comes to manipulating your corpus data.