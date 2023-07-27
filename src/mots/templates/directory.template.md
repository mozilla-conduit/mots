{# This Source Code Form is subject to the terms of the Mozilla Public #}
{# License, v. 2.0. If a copy of the MPL was not distributed with this #}
{# file, You can obtain one at <https://mozilla.org/MPL/2.0/>. #}

<!-- This file was automatically generated using `mots export`.

  See https://mots.readthedocs.io/en/latest/#quick-start for quick
start documentation and how to modify this file. -->

{% macro module_entry(module, is_submodule=False) -%}
{{ "###" if not is_submodule else "####" }} {{ module.name }}

{% if module.description %}
{{ module.description|escape_for_md|trim|wordwrap }}
{% endif %}

{% if not module.owners %}
```{warning}
    This module does not have any owners specified.
```
{% endif %}
```{list-table}
---
stub-columns: 1
widths: 30 70
---
{% if module.owners %}
* - Owner(s)
  -{{ module.owners|format_people_for_md(indent=4) }}
{% endif %}
{% if module.peers %}
* - Peer(s)
  -{{ module.peers|format_people_for_md(indent=4) }}
{% endif %}
{% if module.meta.owners_emeritus %}
* - Owner(s) Emeritus
  - {{ module.meta.owners_emeritus|format_emeritus }}
{% endif %}
{% if module.meta.peers_emeritus %}
* - Peer(s) Emeritus
  - {{ module.meta.peers_emeritus|format_emeritus }}
{% endif %}
{% if module.includes %}
* - Includes
  -{{ module.includes|format_paths_for_md(directory=directory, indent=4) }}
{% endif %}
{% if module.excludes %}
* - Excludes
  -{{ module.excludes|format_paths_for_md(directory=directory, indent=4) }}
{% endif %}
{% if module.meta.group %}
* - Group
  - {{ module.meta.group|trim }}
{% endif %}
{% if module.meta.url %}
* - URL
  - {{ module.meta.url|trim }}
{% endif %}
{% if module.meta.components %}
* - Bugzilla Components
  - {{ module.meta.components|join(", ")|wordwrap|indent(width=4) }}
{% endif %}
{% if module.meta.review_group %}
* - Review Group
  - {{ module.meta.review_group|trim|format_review_group_for_md }}
{% endif %}
```
{% endmacro %}


# Governance

## Overview

To add, remove, or update module information, see the
[mots documentation](https://mots.readthedocs.io/en/latest/#adding-a-module>).

{{ directory.description|wordwrap }}


## Modules

{% for module in directory.modules -%}
{{ module_entry(module) }}
{% if module.submodules %}
{% for submodule in module.submodules %}
{{ module_entry(submodule, True) }}

{% endfor %}
{% endif %}
{% endfor %}
