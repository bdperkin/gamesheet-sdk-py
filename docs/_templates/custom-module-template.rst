{#
===============================================================================
Custom Sphinx Autosummary Template for Modules
===============================================================================
This Jinja2 template controls how autosummary generates documentation pages
for Python modules. It's used when a module is referenced in an autosummary
directive with ``:template: custom-module-template.rst``.

Template Context Variables (provided by Sphinx autosummary):
  - fullname: Fully qualified module name (e.g., 'gamesheet_sdk.auth.session')
  - attributes: List of module-level attribute names
  - functions: List of function names in the module
  - classes: List of class names in the module
  - exceptions: List of exception class names in the module
  - modules: List of submodule names

Jinja2 Filters:
  - escape: Escapes special reStructuredText characters
  - underline: Creates a section underline of the appropriate length
  - _(string): Translation function for internationalization

This template generates a page with:
  1. Module name as title (underlined with '=')
  2. automodule directive to document the module docstring
  3. Module Attributes rubric with autosummary table (if any exist)
  4. Functions rubric with autosummary table (if any exist)
  5. Classes rubric with autosummary table (if any exist)
     - Classes use the custom-class-template.rst for their own pages
  6. Exceptions rubric with autosummary table (if any exist)
  7. Submodules section with recursive autosummary (if any exist)

The ``:toctree:`` option in autosummary directives tells Sphinx to generate
separate pages for each item and add them to the table of contents.

The ``:nosignatures:`` option hides function/method signatures in the summary
table (full signatures appear on the individual detail pages).

See: https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html
#}
{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Module Attributes') }}

   .. autosummary::
      :toctree:
   {% for item in attributes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block functions %}
   {% if functions %}
   .. rubric:: {{ _('Functions') }}

   .. autosummary::
      :toctree:
      :nosignatures:
   {% for item in functions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block classes %}
   {% if classes %}
   .. rubric:: {{ _('Classes') }}

   .. autosummary::
      :toctree:
      :template: custom-class-template.rst
      :nosignatures:
   {% for item in classes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block exceptions %}
   {% if exceptions %}
   .. rubric:: {{ _('Exceptions') }}

   .. autosummary::
      :toctree:
   {% for item in exceptions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

{% block modules %}
{% if modules %}
.. rubric:: Submodules

.. autosummary::
   :toctree:
   :template: custom-module-template.rst
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}
