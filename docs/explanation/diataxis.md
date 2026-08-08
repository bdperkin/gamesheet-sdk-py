# Why these docs are organized into four quadrants

This project's documentation is structured following the [Diátaxis framework](https://diataxis.fr/), authored by Daniele Procida.

Diátaxis observes that effective technical documentation serves four _distinct_ user needs that cannot be merged without harm:

|                      | **Practical steps** | **Theoretical knowledge** |
| -------------------- | ------------------- | ------------------------- |
| **Study (learning)** | Tutorials           | Explanation               |
| **Work (doing)**     | How-to guides       | Reference                 |

When you sit down to write something for these docs, the first question is _which of the four quadrants does it belong in?_ — and if the answer is "more than
one," that's usually a signal that the content needs to be split.

## 1. Why this matters

When a single page tries to teach, demonstrate, document, and explain all at once, it does each of those jobs badly. A user who came for a quick lookup has to
wade through pedagogy; a learner gets dropped into reference material before they have context.

Splitting by _user need_ keeps each page focused. The cross-references between quadrants then carry the cognitive load instead of the prose.

## 2. How to choose a quadrant

Ask yourself, _about the reader who will land on this page:_

- Are they **trying to learn the SDK** by following along? → {doc}`../tutorials/index`
- Do they have **a specific task in mind** and need a recipe? → {doc}`../how-to/index`
- Do they need to **look something up** while doing their work? → {doc}`../reference/index`
- Do they want **deeper understanding** of why something is the way it is? → this section ({doc}`index`)

If two of those are tied, the content probably needs to be two pages, one in each quadrant, cross-linking to the other.

## 3. Further reading

- [diataxis.fr](https://diataxis.fr/) — the canonical introduction
- [The four kinds of documentation, and why](https://docs.divio.com/documentation-system/) — an earlier write-up by the same author
