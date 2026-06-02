# How-to guides

> A how-to guide is a recipe; it serves a reader who **already has enough context to understand the problem and the solution**.
>
> — [diataxis.fr/how-to-guides](https://diataxis.fr/how-to-guides/)

How-to guides are **task-oriented**. The reader has a specific goal in mind and wants the shortest path to it. They are not beginners — they
understand the building blocks; they just need a recipe.

## Authoring guidance

When adding a how-to guide to this section:

- **State the goal in the title.** ("How to authenticate against the GameSheet WebUI", not "Authentication".)
- **Skip pedagogy.** Assume the reader already understands the SDK's building blocks. Cross-link {doc}`../explanation/index` when context is
  essential.
- **Stay focused.** The guide solves _one_ problem. If you find yourself branching, split the guide.
- **Pick sensible defaults and move on.** Walking through alternative configurations is the job of a {doc}`tutorial <../tutorials/index>`.

```{toctree}
:maxdepth: 1

install-in-github-actions
cut-a-release
```
