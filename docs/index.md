`buzz` is a Python library for parsing and analysing natural language.

It relies heavily on *pandas*, *numpy*, and occasionally *NLTK*. Dependency parsing is done by *spaCy*, and dependency searching is handled by a purpose-built library called [*depgrep*](https://github.com/interrogator/depgrep). Almost all major data structures are based on Pandas' DataFrames, so you can use that functionality for anything that isn't already provided by *buzz*.

Note that a shorter, general introduction to *buzz* is available [via GitHub](https://github.com/interrogator/buzz). This site provides more comprehensive documentation.

## *buzz*: table of contents

- [Installation](install.md)
- [Modelling and parsing corpora](corpus.md)
- [Exploring parsed datasets](dataset.md)
- [Processing raw strings](from_string.md)
- [Generating tables](table.md)
- [Concordancing](conc.md)
- [Measuring prototypicality and similarity](proto.md)
- [Working with pandas](pandas.md)
- [Interactive visualisation in the browser](site.md)
- [Case study: lexical density](density.md)

## A web-app for buzz (buzzword)

For a web-app based on *buzz*, called *buzzword*, head [here](https://buzzword.readthedocs.io/en/latest/). If you're not such a strong programmer, but want to be able to use the core features of *buzz*, then this is likely the project for you. This code is open-source, and I can help you get it running on your university server with the datasets you want to be able to explore.

## Free and open software

Pull requests are always welcome for both buzz and buzzword. I believe they can address a lot of shortcomings in available tools for research into natural language, and welcome any collaboration you might want to offer.
