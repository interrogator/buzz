# Working with pandas

`buzz` keeps everything in DataFrame-like objects, so you can use the powerful pandas syntax whenever you like.


## Monkey-patching the Dataset

Just as you can with pandas, you can also write your own methods, and monkey-patch them to the Dataset object:

```python
from buzz import Dataset

def no_punct(df):
    return df.skip.wordclass.PUNCT

Dataset.no_punct = no_punct
```