# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# NOTE: This module is intended to be copied and renamed to
# "integration_queue_job" before use. See README.md for full instructions.

{
    'name': 'Integration Queue Job Bridge (OCA)',
    'summary': '''Compatibility bridge that allows VentorTech integration connectors
to work with OCA\'s Job Queue module instead of the built-in integration_queue_job fork.
''',
    'version': '19.0.1.0.0',
    'author': 'VentorTech',
    'website': 'https://github.com/ventor-dev/integration-queue',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': ['queue_job'],
    'installable': True,
    'application': False,
    'maintainers': ['ventor-dev'],
    'post_init_hook': 'post_init_hook',
}
