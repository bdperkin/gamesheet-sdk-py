# Reference

> Reference guides are **technical descriptions of the machinery and how to operate it**. They are information-oriented, austere, and to the point.
>
> — [diataxis.fr/reference](https://diataxis.fr/reference/)

Reference is **information-oriented**. It describes the SDK as it actually is — every module, class, function, and CLI option — so that users can look
things up while doing their work. It does not teach, it does not motivate, and it does not solve problems. {doc}`Other quadrants <../index>` do those
jobs.

Most of this section is generated from source by `sphinx.ext.autodoc`, `sphinx.ext.autosummary`, and `sphinx-argparse`, so it cannot drift from the
shipped binary.

## Authoring guidance

Hand-written reference pages should:

- **Mirror the structure of the thing they describe.** A reference page about module `foo.bar` should be findable at `reference/foo.bar`.
- **Be exhaustive within their scope.** Half-documented APIs are worse than no docs — users assume the page is complete.
- **Stay descriptive.** Don't tell the reader what they _should_ do; tell them what the code _does_. Recommendations live in {doc}`../how-to/index` or
  {doc}`../explanation/index`.

```{toctree}
:maxdepth: 2

api
cli
supported-configurations
```
