# Concordancing

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
| *metadata*         |  True       |  Add metadata info as extra columns                        |



