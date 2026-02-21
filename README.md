# Integration Queue — Background Jobs for VentorTech Connectors

This repository provides background job processing support for
[VentorTech e-commerce connectors](https://ventor.tech) (WooCommerce,
PrestaShop, Magento 2, Shopify) on Odoo 19.0.

It contains **two modules** with different purposes:

---

## Modules

### `integration_queue_job` — Standalone Fork

A self-contained background jobs module forked from
[OCA's Job Queue](https://github.com/OCA/queue).  This is the **default
dependency** of VentorTech connectors and the simplest option when OCA's
`queue_job` is **not** already installed in your environment.

**Use this module when:**
- You are installing VentorTech connectors on a fresh Odoo instance.
- OCA's `queue_job` is not already present in your add-on path.

---

### `integration_queue_job_bridge` — OCA Compatibility Bridge

A lightweight shim that delegates everything to OCA's
[`queue_job`](https://github.com/OCA/queue) module.  It creates the XML-ID
aliases that VentorTech connector modules rely on so that **no changes are
needed** in any connector module when switching from the standalone fork to
OCA's implementation.

**Use this module when:**
- OCA's `queue_job` is already installed (or preferred) in your environment.
- You want to avoid maintaining a fork and stay on the official OCA module.

---

## Switching from `integration_queue_job` to OCA `queue_job`

Follow these steps to replace the standalone fork with OCA's module while
keeping all VentorTech connectors working without any code changes.

### Prerequisites

- OCA's `queue_job` module (Odoo 19.0 branch) available in your add-on path.
  Repository: https://github.com/OCA/queue

### Step-by-step

1. **Copy and rename the bridge module.**

   Copy `integration_queue_job_bridge` from this repository into your Odoo
   add-ons directory and rename the copy to `integration_queue_job`:

   ```bash
   cp -r integration_queue_job_bridge /path/to/your/addons/integration_queue_job
   ```

   The technical name **must** be `integration_queue_job` because that is the
   name referenced in all VentorTech connector manifests and XML files.

2. **Uninstall the old standalone module.**

   In Odoo's Apps menu, uninstall `Integration Queue Job` (the standalone
   fork).  Odoo will also uninstall all VentorTech connector modules that
   depend on it — this is expected.

3. **Install OCA's `queue_job`.**

   Install the OCA *Job Queue* module from your add-ons list.

4. **Install the bridge (renamed to `integration_queue_job`).**

   Install the module you renamed in step 1.  Its `post_init_hook` will
   automatically create the XML-ID aliases that connectors need
   (`integration_queue_job.channel_root`,
   `integration_queue_job.group_queue_job_manager`).

5. **Reinstall VentorTech connectors.**

   Reinstall the connector modules (e.g. *Odoo E-Commerce Connector Core* and
   any specific connector like WooCommerce or Shopify).  No changes to their
   manifest, XML, or Python files are required.

### What the bridge does internally

The bridge's `post_init_hook` creates `ir.model.data` alias records:

| Alias XML ID | Points to |
|---|---|
| `integration_queue_job.channel_root` | `queue_job.channel_root` |
| `integration_queue_job.group_queue_job_manager` | `queue_job.group_queue_job_manager` |

These aliases make every XML `ref=`, `groups=`, and Python `env.ref()` call
that uses the `integration_queue_job.*` prefix resolve to the correct records
owned by OCA's module — transparently and without touching any connector code.

---

## License

LGPL-3.0 or later — see individual file headers for full copyright notices.
