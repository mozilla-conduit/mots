{# This Source Code Form is subject to the terms of the Mozilla Public #}
{# License, v. 2.0. If a copy of the MPL was not distributed with this #}
{# file, You can obtain one at https://mozilla.org/MPL/2.0/.           #}
..
    This file was automatically generated using `mots export`.
{%- macro module_entry(module, is_submodule=False) -%}
{{ module.name }}
{{ "~" * module.name|length if not is_submodule else "=" * module.name|length }}
{% if module.description %}
{{ module.description|escape_for_rst }}
{% endif %}

{% if not module.owners %}
.. warning::
    This module does not have any owners specified.
{% endif %}

.. list-table::
    :stub-columns: 1

{% if module.owners %}
    * - Owner(s)
      - {{ module.owner_names|join(", ") }}
{% endif %}
{% if module.peers %}
    * - Peer(s)
      - {{ module.peer_names|join(", ") }}
{% endif %}
{% if module.includes %}
    * - Includes
      - {{ module.includes|join(", ")|escape_for_rst }}
{% endif %}
{% if module.excludes %}
    * - Excludes
      - {{ module.excludes|join(", ")|escape_for_rst }}
{% endif %}
{% if module.meta.group %}
    * - Group
      - {{ module.meta.group }}
{% endif %}
{% if module.meta.url %}
    * - URL
      - {{ module.meta.url }}
{% endif %}
{% if module.meta.components %}
    * - Bugzilla Components
      - {{ module.meta.components|join(", ") }}
{% endif %}
{% endmacro %}


=======
Modules
=======

{{ directory.description|escape_for_rst + "\n" }}

{%- for module in directory.modules -%}
{{ module_entry(module) }}
{% if module.submodules %}
{% for submodule in module.submodules %}
{{ module_entry(submodule, True) }}
{% endfor %}
{% endif %}
{% endfor %}
