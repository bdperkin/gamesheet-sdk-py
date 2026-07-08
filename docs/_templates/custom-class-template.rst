{#
===============================================================================
Custom Sphinx Autosummary Template for Classes
===============================================================================
This Jinja2 template controls how autosummary generates documentation pages
for Python classes. It's used when a class is referenced in an autosummary
directive with `:template: custom-class-template.rst`.

Template Context Variables (provided by Sphinx autosummary):
  - fullname: Fully qualified class name (e.g., 'gamesheet_sdk.auth.AuthenticatedSession')
  - module: Module name (e.g., 'gamesheet_sdk.auth')
  - objname: Object name without module (e.g., 'AuthenticatedSession')
  - name: Same as fullname
  - methods: List of method names
  - attributes: List of attribute names

Jinja2 Filters:
  - escape: Escapes special reStructuredText characters
  - underline: Creates a section underline of the appropriate length

This template generates a page with:
  1. Class name as title (underlined with '=')
  2. currentmodule directive for cross-references
  3. autoclass directive with member display options
  4. Methods rubric with autosummary table (if methods exist)
  5. Attributes rubric with autosummary table (if attributes exist)

See: https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html
#}
{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:
   :show-inheritance:
   :inherited-members:
   :special-members: __init__, __call__

   {% block methods %}
   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
      :nosignatures:
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}
