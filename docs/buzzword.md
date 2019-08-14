# buzzword: a web app for corpus linguistics

> *buzz* comes bundled with a graphical interface, *buzzword*, which allows you to interact with parsed/annotated corpora in your browser. Using *buzz* as a backend, *buzzword* provides the ability to perform complex searches, make frequency tables, generate interactive visualisations and build concordances.

## Running locally

To run the tool locally, you'll want to have at least one parsed corpus ready to analyse. To do this, first, parse a corpus if you don't already have one parsed:

```bash
python -m buzz.parse --cons-parser none ./path/to/data
```

After this, you should configure a `corpora.json`, which tells the tool which corpora will be loaded into the tool. Copy `corpora.json.example` as `corpora.json` and modify it to contain the corpora you want to show in the app.

Then, you need to choose if you'd like to configure global settings via a `.env` file or command line options. If you want to use a `.env` file, copy `.env.example` to `.env`, and change settings as you like. Most importantly, make sure `BUZZWORD_CORPORA_FILE` is set to the path for your `corpora.json`.

If a value isn't configured in `corpora.json`, the tool will look to `.env` or the provided command line options.

Once these files are set up, you can start the tool with:

```bash
python -m buzz.word
# or
buzzword
```

With either command, you can also enter any the following options:

```
# global settings
--corpora-json          : corpora.json : path to corpora.json file used to load corpora
--no-load / -nl         : false        : do not load the full corpus into memory (for very large datasets/small machines, makes searches much slower)
--page-size / -p        : 25           : Rows per page of table
--env / -e              : none         : Use .env for configuration (pass path to .env file)
--debug                 : true         : run flask/dash in debug mode

# settings overridden by corpora.json

--drop-columns / -d     : none         : Comma separated list of corpus columns to drop before loading into tool
--max-dataset-rows / -m : none         : Cut corpus at this many lines before loading into tool
--table-size / -s       : 2000,200     : Max rows,columns to show in tables
--add-governor / -g     : false        : add governor token features to dataset. Slow to load and consumes more memory, but allows searching/showing governor features
```

If you pass a value for `--env`, make sure all settings are in your `.env` file.

## Start page

The main page of the tool allows you to select a pre-loaded corpus, or upload your own. If you want to browse a pre-loaded corpus, simply click its name in the table.

If you want to upload your own, you need to add files to the file input box. If you add plain text files, the tool will automatically parse them. If you add `.conll` or `.conllu` files, the tool will assume they are in `CONLL-U v2` format and attempt to load them without any kind of conversion.

Once you've added files, simply provide a name for your corpus, and select its language. Then, hit `Upload and parse`. Once the parsing is finished, a link to the new corpus will appear. Click it to explore the corpus in the `Explore` view.

## Dataset view

In this view, you can see the loaded corpus, row by row, with its token and metadata features. Like the other tables in *buzzword*, the table is interactive: you can filter, sort and remove rows and columns as you wish. To filter, just enter some text into one of the blank cells above the first table row. More advanced kinds of filtering strings are described [here](https://dash.plot.ly/datatable/filtering).

### Searching

The dataset tab is also the place where you search the corpus. In *buzzword*, because you can search within search results, the best way to find what you're looking for is usually to "drill-down" into the data by searching multiple times, rather than writing one big, complicated query.

In the leftmost dropdown field, you select the feature you want to search (word form, lemma form, POS, etc). Each of these options targets a token or metadata feature, except *Dependencies*, which is used to search the dependency grammar with which a corpus has been parsed.

To start out, select something simple, like 'Word', so that your search string will be compared to the word as it was writtin in the original, unparsed text.

In the text entry field, you neeed to provide a case-sensitive regular expression that you want to match. The only exception to this is if you are searching *Dependencies*, in which case you will need to use [the depgrep query language](https://github.com/interrogator/depgrep). If you're new to regular expressions, and just want to find words that exactly match a string, enter `^word$`. The caret (`^`) denotes 'start of string', and the dollar sign (`$`) denotes the end of string. Without the dollar sign, the query would match not only *word*, but *wordy*, *wording*, *word-salad*, and so on.

Finally, you can toggle result inversion using the toggle switch (i.e. return rows *not matching* the search criteria). Then, hit *Search*. Search time depends mostly on how many items are returned, though very complex *depgrep* queries can also take a few seconds.

When the search has completed, the table in the Dataset Tab will be reduced to just those rows that match your query. At the top of the tool, you'll see that your search has entered into the "Search from" space, translated into something resembling natural English. Beside the search is a bracketed expression telling you how many results you have. This component has the format:

`(absolute-frequency/percentage-of-parent-search/percentage-of-corpus)`

Whatever is selected in the *Search from* dropdown is the dataset to be searched. Therefore, if you search again with the current search selected, you will "drill down", removing more rows as you go. So, if you are interested in nouns ending in *ing* that do not fill the role of *nsubj*, you can search three times:

1. Wordclass matching `NOUN`
2. Word matching `ing$`
3. Function mtching `nsubj`, inverted

Alternatively, you could write one *depgrep* query:

```
X"NOUN" = w/ing$/ != F"nsubj"
```

If you want to learn to use the *depgrep* language, check out [its documentation on GitHub](https://github.com/interrogator/depgrep).

At any time, if you want to delete your search history, you can use the 'Clear history' button to forget all previous searches.

## Frequencies view

In contrast to other tools, *buzzword* separates the processes of searching datasets and displaying their results. This gives you the flexibility to display the same search result in different ways, without the need for performing duplicated searches.

So, once you are happy with a search result generated in the *Dataset* tab, you can move to the *Frequencies* tab to transform your results into a frequency table.

To generate a frequency table, start by searching the correct search from the *Search from* dropdown menu at the top of the tool. These are the results you will be calculating from. You can select either the entire corpus, or a search result generated in the *Dataset* tab.

Next, you need to choose which feature or features you want to use as the column(s) of the table. Multiple selections are possible; for example, you can select `Word` and then `Wordclass` to get results in the form: `happy/ADJ`.

After selecting columns, select which feature should serve as the index of the table. You don't have to use `Filename` here: you can model things like *lemma form by speaker* or *Functions by POS*. Multiple selections are not possible here.

Next, choose how you would like to sort your data. By default, the most frequent items appear first. But, you can sort by infrequent (i.e. reverse total), alphabetically, and so on. Particularly special here are *increase* and *decrease*. These options use linear regression to figure out which items become comparatively more common from the first to last items on the x-axis. They are particularly useful when your choice for table index is sequential, such as chapters of a book, scenes in a film, or dates.

Finally, choose what kind of calculation you would like. The default, *Absolute frequency*, simply counts occurrences. You can also choose to model relative frequencies, using either this search or the entire corpus as the denominator. What this means is that if you have searched for all nouns, you can calculate the relative frequency of each noun relative to all nouns (*Relative of result*), or each noun relative to all tokens in the corpus (*Relative of corpus*).

Alternatively, you can also choose to calculate keyness, rather than absolute/relative frequency. Both [log-likelihood](http://ucrel.lancs.ac.uk/llwizard.html) and percentage-difference measures are supported. These measures are particularly useful as means to find out which tokens are unexpectedly frequent or infreuent in the corpus.

Once you've chosen your parameters, hit *Generate table* to start the tabling process. Like searching, the calculations themselves are fairly fast. What might take some time, however, is displaying a result with many rows/columns. So, bear in mind when tabling that some choices can lead to unmanageably large results: if you choose to display *Word*, *Filename*, *Sent #* and *Token #* as columns, for example, you will be generatng a column for every single token in the corpus.

### Editing the *Frequencies* table



## Chart view

Once you have a table representing the results you're interested in, you can go to the Chart tab to visualise the result.

Visualisation is easy: just select the plot type, the number of items to display, and whether or not you want to transpose

Figures are interactive, so go ahead and play with the various tools that appear above the charts.

Note that there are multiple chart spaces. Just click '*Chart #1*' to fold this space in and out of view. Each space is completely independent from the others. You can therefore visualise completely different things in each.

## Concordance view

Concordancing, or Keyword-in-context, aligns search result matches in a column, displaying their co-text on either side. To generate a concordance, first, select the data you want to visualise from the *Search from* dropdown menu at the top of the page. Then, select how you would like to format your matches. Like when making frequency tables, you can format matches using multiple token features. One popular combination is *word/POS*, but there are plenty more combinations that might be useful, too!
