# Creating corpora

> On this page, you will learn how to build the metadata-rich corpora that work best with *buzzword*.

## Basics: an unannotated corpus

At the very minimum, *buzzword* can accept a single file of plain text. For example, you could create a file, `joke.txt`, containing the following text:

```text
A lion and a cheetah decide to race.      
The cheetah crosses the finish line first.
"I win!"
"You're a cheetah!"
"You're lion!"
```

Once you upload it, the file will be run through a processing pipeline, which will split the text into sentences and tokens, and then annotate with POS tags, wordclasses, and dependency grammar annotations. This is already a good start: you can do all kinds of frequency calculation, concordancing and visualisation with just this plain text. However, where *buzzword* really excels is in handling large, metadata-rich datasets. So, let's go through the process of building such a corpus now.

## Multiple files

**buzzword** accepts multiple files as input. Using multiple files is a quick and easy way to add metadata into your corpus: once uploaded, you will be able to explore language use by file, or filter data by file to dynamically create subcorpora.

Therefore, the best way to use files is to give them a name that is both sequential and categorical. So, let's rename `joke.txt` to `001-joke-lion-pun.txt`. Just by doing this, we will later be able to filter by pun jokes, by lion jokes, or visualise language change from our first to our last joke.

```text
jokes
├── 001-joke-lion-pun.txt
├── 002-joke-soldier-knock-knock.txt
└── ... etc.
```

## Adding metadata: speaker names

Now, let's add some metadata within our corpus files in a format that *buzzword* can understand. First (and simplest), we add speaker names at the start of lines. Like filenames, any like other annotations we may add, these speaker names will end up in the parsed corpus, allowing us to filter the corpus, calculate stats, and visualise data by speaker.

```text
A lion and a cheetah decide to race. 
The cheetah crosses the finish line first.
CHEETAH: I win!
LION: You're a cheetah!
CHEETAH: You're lion!
```

Speaker names should be provided in capital letters, using underscores or hyphens instead of spaces. Not all lines need speaker names.

### File-level metadata

Next, we can begin adding metadata in XML format. XML is much richer and better structured than plain text, allowing a great deal of precision. To add metadata that applies to an entire file, you need to create an XML element `<meta>` on the first line of the file:


```xml
<meta doc-type="joke" rating=6.50 speaker="NARRATOR"/>
A lion and a cheetah decide to race. 
The cheetah crosses the finish line first.
CHEETAH: I win!
LION: You're a cheetah!
CHEETAH: You're lion!
```

Best practice here is to use lower-cased names and hyphens, and to use quotation marks for string values. 

File-level metadata will be applied to every single sentence (and therefore, every token) in the file. Therefore, though we've defined `speaker` both in XML and in script-style, that's no problem: `NARRATOR` will be applied to every line, but overwritten by `CHEETAH` and `LION` where they appear. This means that in general, you can use the file-level metadata to provide overwritable defaults, rather than adding the value to each line.

### Sentence annotation

Going one step further, we can add sentence-level metadata using XML elements at the end of lines, in exactly the same format as before.

```xml
<meta doc-type="joke" rating=6.50 speaker="NARRATOR"/>
A lion and a cheetah decide to race. <meta move="setup" dialog=false punchline=false some-schema=9 />
The cheetah crosses the finish line first. <meta move="setup" dialog=false punchline=false />
CHEETAH: I win! <meta move="middle" dialog=true some-schema=2 />
LION: You're a cheetah! <meta move="punchline" funny=true dialog=true some-schema=3 />
CHEETAH: You're lion! <meta move="punchline" funny=true dialog=true some-schema=4 rating=7.8 />
```

This more fine-grained metadata is great for discourse-analytic work, such as counting frequencies by genre stages of a text (i.e. joke setup vs. punchline).

### Span and token annotation

Finally, to complete our annotations, let's also add some span and token level metadata:

```xml
<meta doc-type="joke" rating=6.50 speaker="NARRATOR"/>
<meta ent-type="animal">A lion</meta> and <meta ent-type="animal">a cheetah</meta> decide to race. 
<meta move="setup" dialog=false punchline=false some-schema=9 />
The cheetah crosses the finish line first. <meta move="setup" dialog=false punchline=false />
CHEETAH: I win! <meta move="middle" dialog=true some-schema=2 />
LION: You're a <meta play-on="cheater">cheetah</meta>! <meta move="punchline" funny=true dialog=true some-schema=3 />
CHEETAH: You're <meta play-on="lying">lion</meta>! <meta move="punchline" funny=true dialog=true some-schema=4 rating=7.8 />
```

So, we've gone a bit overboard here, tagging `a lion` and `a cheetah` spans with a custom `ent-type` annotation, and clarifying the puns in the punchline. Notice that you can enclose multiple tokens inside `<meta>` elements, which is useful for labelling entire nominal and verbal groups, for example.

### Summary

Available metadata formats are:

1. File level metadata (XML on the first line)
2. Sentence level metadata (XML at end of sentences)
3. Span/token level metadata (XML elements containing one or more tokens)
4. Speaker names in script style

* XML annotations values can be strings, integers, floats and booleans will all be understood by the tool.
* Metadata is always inherited, from file, to sentence, to span and token level. The `rating` for the whole file will be replaced for the final sentence with `7.8`.
* If a field is missing in one of the metadata, it will end up with a value of `None` in the parsed corpus. 

Once parsed, the first sentence of the underlying dataset will modelled as something like:

| File     | Sent   | Token   | Word    | Lemma   | Wordclass   | Part of speech   |   Governor index | Dependency role   | e   | dialog   | doc_type   |   ent_id | ent_iob   | ent_type   | funny   | move   | play_on   | punchline   |   rating |   sent_id |   sent_len |   some_schema | Speaker   |
|------|----|----|---------|---------|-------------|------------------|------------------|-------------------|-----|----------|------------|----------|-----------|------------|---------|--------|-----------|-------------|----------|-----------|------------|---------------|-----------|
| text |  1 |  1 | A       | a       | DET         | DT               |                2 | det               | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  2 | lion    | lion    | NOUN        | NN               |                6 | nsubj             | _   | False    | joke       |        0 | O         | animal     | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  3 | and     | and     | CCONJ       | CC               |                2 | cc                | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  4 | a       | a       | DET         | DT               |                5 | det               | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  5 | cheetah | cheetah | NOUN        | NN               |                2 | conj              | _   | False    | joke       |        0 | O         | animal     | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  6 | decide  | decide  | VERB        | VBP              |                0 | ROOT              | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  7 | to      | to      | PART        | TO               |                8 | aux               | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  8 | race    | race    | VERB        | VB               |                6 | xcomp             | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |
| text |  1 |  9 | .       | .       | PUNCT       | .                |                6 | punct             | _   | False    | joke       |        0 | O         |            | _       | setup  | _         | False       |      6.5 |         1 |          9 |             9 | NARRATOR  |

## Next steps

Once you have a corpus, be it one or many files, annotated or unannotated, you are ready to feed it to *buzzword*. Simply drag and drop or click to upload your files, give your corpus a name, select a language, and hit `Upload and parse`. 

Once the parsing is finished, a link to the new corpus will appear. Click it to explore the corpus in the `Explore` page. Click [here](/guide) for instructions on how to use the *Explore* page.