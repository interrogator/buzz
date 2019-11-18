# Generating interactive websites

*buzz* interfaces smoothly with [dash](https://dash.plot.ly), a tool that builds simple websites for exploring datasets. Charts are responsive, interactive and beautiful.

On any `Table` or Dataset object, you can run `df.site("Site title")` to generate a site accessible via your web browser at `http://127.0.0.1:8050/`.

This returns a `DashSite` object, which you can then extend and refine. Generating a simple site works like so:

```python
corpus = Corpus("dtrt/do-the-right-thing-parsed").load()
verbs = corpus.just.wordclass.VERB
tab = verb.table(relative=True, sort="total")
site = tab.site('Verbs in "Do the right thing')
```

## Adding components to the site

The `site.add` method is how you add content to your site.

Pass in the name of the component type you want to add, followed by the content (i.e. a string of text/markdown, or a *buzz* object such as a concordance of frequency table)

```python
# add heading and text
site.add("h2", "New heading")
site.add("div", "Text <i>below</i> the heading")
# or, use markdown to combine both:
site.add("markdown", "## New heading\n\nText *below* the heading")
```

Many different types of chart are possible. They can be added to the site by passing the chart type, alongside a DataFrame-like object.

```python
site.add("line", verbs)
site.add("bar", verbs)
site.add("stacked_bar", verbs)
site.add("pie", verbs)
site.add("heatmap", verbs)
site.add("area", verbs)
```

For a concordance, use `conc`:

```python
site.add("conc", verbs.conc(show=['w', 'l']))
```

## Customising style

*dash* allows you to easily pass in a lot of HTML and CSS style as you are generating your page. Full documentation on this is still in the works.

```python
style = {'textAlign': 'center', 'color': '#7FDBFF'}
site.add('div', 'Some text with style added', style=style)
```

## Starting and stopping the site

New content should immediately be visible in the web browser (or, you may need to hit refresh). To control the site itself, you can use:

```python
site.run()
site.kill()
site.reload()
```

## Building from scratch

You can also build a site from scratch by importing `DashSite` and adding components as you like:

```python
from buzz.dashview import DashSite
site = DashSite("My data exploration")
markdown = "> This site shows my key findings\n\n## A concordance for `person`:"
site.add("markdown", markdown)
conc = corpus.just.lemma.PERSON.conc(show=["w", "l"])
site.add("conc", conc)
site.add("h4", "Summary")
site.add("div", "Thank you for reading!")
```

## Roadmap

*dash* should make it possible to allow all kinds of functionality, such as searching and generating components from within the page itself.

Eventually, I'd also like it to be possible to create, save and easily deploy your site so that it can be viewed from anywhere.

Combining these two ideas, I think it'd be wonderful if you could serve your dataset alongside an interface for concordancing, plotting, and so on.


