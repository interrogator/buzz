# buzzword: a web app for corpus linguistics

> *buzz* comes bundled with a graphical interface, *buzzword*, which allows you to interact with parsed/annotated corpora in your browser. Using *buzz* as a backend, *buzzword* provides the ability to perform complex searches, make frequency tables, generate interactive visualisations and build concordances.

## Running locally

```bash
python -m buzz.word ./path-to-parsed-corpus
# or
buzzword ./path-to-parsed-corpus
```

Either command gives you the following options:

```
--no-load / -nl         : false    : do not load the full corpus into memory (for very large datasets/small machines, makes searches much slower)
--title / -t            : buzzword : Custom title for the app
--drop-columns / -d     : none     : Comma separated list of corpus columns to drop before loading into tool
--max-dataset-rows / -m : none     : Cut corpus at this many lines before loading into tool
--table-size / -s       : 2000,200 : Max rows,columns to show in tables
--page-size / -p        : 25       : Rows per page of table
--env / -e              : none     : Use .env for configuration (pass path to .env file)
--debug                 : true     : run flask/dash in debug mode
```

## Dataset view

In this view, you can see the loaded corpus, row by row, with its token and metadata features. Like the other tables in *buzzword*, the table is interactive: you can filter, sort and remove rows and columns as you wish.

The dataset tab is also the place where you search the corpus. In *buzzword*, the best way to search is to "drill-down" into the data by searching multiple times.

In the leftmost dropdown field, you select the feature you want to search (word form, lemma form, POS, etc). Each of these options targets a token or metadata feature, except *Dependencies*, which is used to search the dependency grammar with which the corpus has been parsed. To start out, select something simple, like 'Word'.

In the text entry field, provide a case-sensitive regular expression that you want to match. If you are searching dependencies, use the depgrep query language. If you're new to regular expressions, and just want to find words that exactly match a string, enter `^word$$`. The caret (`^`) denotes 'start of string', and the dollar sign (`$`) denotes the end of string. Without the dollar sign, the query would match not only *word*, but *wordy*, *wording*, *word-salad*, and so on.

Finally, you can toggle result inversion using the toggle switch (i.e. return rows *not matching* the search criteria). Then, hit *Search*. Search time depends mostly on how many items are returned.

When the search has completed, the table will be reduced to just the matching rows. At the top of the tool, you'll see that your search has entered into the "Search from" space, translated into natural English. If you search again with the current search selected, you will "drill down", removing more rows as you go.

So, if you are interested in nouns ending in 'ing' that do not fill the role of *nsubj*, You search three times:

1. Wordclass matching `NOUN`
2. Word matching `ing$`
3. Function mtching `nsubj`, inverted

If you want to reset your search history, you can use the 'Clear history' button to restart your investigtion.

## Frequencies view

Once you have finished searching, you can move to the Frequenciest tab to turn the results into a frequency table.

Start by searching the correct search from the "Search from" dropdown menu at the top of the tool. These are the results you will be calculating from.

Next, choose which feature or features you want to use as the columns of the table. For example, you can enter `word, wordclass` to get results in the form: `happy/ADJ`.

After selecting columns, select which feature should serve as the index. You don't have to use `Filename` here: you can model things like *lemma form by speaker* or *Functions by POS*.

Next, choose how you would like to sort your data. By default, the most frequent items appear first. But, you can sort by infrequent, alphabetically, and so on. Particularly special here are *increase* and *decrease*. These options use linear regression to figure out which items become comparatively more common from the first to last items on the x-axis.

Finally, choose what kind of calculation you would like. You can keep the default, *Absolute frequency*, or do relative frequency, using either this search or the corpus as the denominator. You can also choose to calculate keyness here. Both log-likelihood and percentage-difference measures are supported.

Hit *Generate table* to start the tabling process. Again, the calculations themselves are fairly fast. What might take some time, however, is displaying a result with many rows/columns.

## Chart view

Once you have a table representing the results you're interested in, you can go to the Chart tab to visualise the result.

Visualisation is easy: just select the plot type, the number of items to display, and whether or not you want to transpose

Figures are interactive, so go ahead and play with the various tools that appear above the charts.

Note that there are multiple chart spaces. Just click '*Chart #1*' to fold this space in and out of view. Each space is completely independent from the others. You can therefore visualise completely different things in each.

## Concordance view

Concordancing, or Keyword-in-context, aligns search result matches in a column, displaying their co-text on either side. To generate a concordance, first, select the data you want to visualise from the *Search from* dropdown menu at the top of the page. Then, select how you would like to format your matches. Like when making frequency tables, you can format matches using multiple token features. One popular combination is *word/POS*, but there are plenty more combinations that might be useful, too!
