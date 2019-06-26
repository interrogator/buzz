Concordancing, also known as Keyword in Context (KWIC), is an efficient way to see how some linguistic phenomenon of interest is behaving in context.

Concordancing works on any Dataset, be it a whole corpus or a search result. For example, to concordance words ending in *-ing*:


```python
from buzz import Corpus
dtrt = Corpus('dtrt/do-the-right-thing-parsed')
ing = dtrt.just.words('ing$')
ing.conc()
```

Below are the keyword arguments accepted by the `conc` method:

| Argument | Default | Purpose                                           |
|----------|---------|---------------------------------------------------|
| *show*     | `['w']` | A list of attributes to show in the match column. |
| *n*         |  `100`       |   Stop after producing this many lines  |
| *window*         |  `'auto'`       |  Size of left and right columns, as integer or tuple of two integers. `auto` will attempt to use your display size intelligently                                    |
| *metadata*         |  `True`       |  Add metadata info as extra columns                        |


```python
ing.head().to_html()
```

<table border="1" class="dataframe" style="white-space: nowrap;">
  <col align="right">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>left</th>
      <th>match</th>
      <th>right</th>
      <th>file</th>
      <th>s</th>
      <th>camera_angle</th>
      <th>line</th>
      <th>loc</th>
      <th>scene</th>
      <th>sent_id</th>
      <th>setting</th>
      <th>speaker</th>
      <th>stage_direction</th>
      <th>text</th>
      <th>time</th>
      <th>voice-delivery</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td style="text-align: right;">K , shows that Mister Señor Love Daddy is actually</td>
      <td>sitting</td>
      <td>in a storefront window . The control booth looks d</td>
      <td>01-we-love-radio-station-storefront</td>
      <td>12</td>
      <td>NaN</td>
      <td>2</td>
      <td>INT</td>
      <td>1</td>
      <td>12</td>
      <td>WE LOVE RADIO STATION STOREFRONT</td>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>True</td>
      <td>The last on your dial, but the first in ya hear...</td>
      <td>DAY</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td style="text-align: right;">s is WE LOVE RADIO , a modest station with a loyal</td>
      <td>following</td>
      <td>, * right in the heart of the neighborhood . The O</td>
      <td>01-we-love-radio-station-storefront</td>
      <td>14</td>
      <td>NaN</td>
      <td>_</td>
      <td>INT</td>
      <td>1</td>
      <td>14</td>
      <td>WE LOVE RADIO STATION STOREFRONT</td>
      <td>_</td>
      <td>True</td>
      <td>This is WE LOVE RADIO, a modest station with a ...</td>
      <td>DAY</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td style="text-align: right;">t . It ya know . This is Mister Señor Love Daddy ,</td>
      <td>doing</td>
      <td>the nasty to ya ears , ya ears to the nasty . I'se</td>
      <td>01-we-love-radio-station-storefront</td>
      <td>20</td>
      <td>NaN</td>
      <td>3</td>
      <td>INT</td>
      <td>1</td>
      <td>20</td>
      <td>WE LOVE RADIO STATION STOREFRONT</td>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>True</td>
      <td>This is Mister Señor Love Daddy, doing the nast...</td>
      <td>DAY</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>3</th>
      <td style="text-align: right;">we hear a station jingle . L - O - V - E RADIO ..</td>
      <td>Doing</td>
      <td>da ying and yang da flip and Doing da ying and yan</td>
      <td>01-we-love-radio-station-storefront</td>
      <td>25</td>
      <td>NaN</td>
      <td>5</td>
      <td>INT</td>
      <td>1</td>
      <td>25</td>
      <td>WE LOVE RADIO STATION STOREFRONT</td>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>True</td>
      <td>Doing da ying and yang da flip and Doing da yin...</td>
      <td>DAY</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td style="text-align: right;">a station jingle . L - O - V - E RADIO .. Doing da</td>
      <td>ying</td>
      <td>and yang da flip and Doing da ying and yang da fli</td>
      <td>01-we-love-radio-station-storefront</td>
      <td>25</td>
      <td>NaN</td>
      <td>5</td>
      <td>INT</td>
      <td>1</td>
      <td>25</td>
      <td>WE LOVE RADIO STATION STOREFRONT</td>
      <td>MISTER SEÑOR LOVE DADDY</td>
      <td>True</td>
      <td>Doing da ying and yang da flip and Doing da yin...</td>
      <td>DAY</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
