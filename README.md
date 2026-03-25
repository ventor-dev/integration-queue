# Integration Queue — Background Jobs for VentorTech Connectors

This repository provides background job processing support for
[VentorTech e-commerce connectors](https://ecosystem.ventor.tech) (WooCommerce,
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

## Using the bridge module

There are two scenarios depending on whether you are doing a fresh install or
migrating an existing environment.

---

### Scenario A — Fresh install (OCA `queue_job` preferred)

Use this path when setting up VentorTech connectors on an instance where OCA's
`queue_job` is already installed or where you prefer it over the standalone
fork.  No uninstallation is required.

**Prerequisites**

- OCA's `queue_job` module (Odoo 19.0 branch) available in your add-on path.
  Repository: https://github.com/OCA/queue

**Steps**

1. **Copy and rename the bridge module.**

   Copy `integration_queue_job_bridge` from this repository into your Odoo
   add-ons directory and rename the copy to `integration_queue_job`:

   ```bash
   cp -r integration_queue_job_bridge /path/to/your/addons/integration_queue_job
   ```

   The technical name **must** be `integration_queue_job` because that is the
   name referenced in all VentorTech connector manifests and XML files.

2. **Install OCA's `queue_job` and the bridge.**

   From the Apps menu, install `queue_job` first, then install the
   `integration_queue_job` module (the bridge you placed in step 1).  Its
   `post_init_hook` will automatically create the XML-ID aliases that
   connectors need (`integration_queue_job.channel_root`,
   `integration_queue_job.group_queue_job_manager`).

3. **Install VentorTech connectors.**

   Install the connector modules (e.g. *Odoo E-Commerce Connector Core* and
   any specific connector like WooCommerce or Shopify) as usual.  No changes
   to their manifest, XML, or Python files are required.

---

### Scenario B — Migrating from the standalone `integration_queue_job`

Use this path when the standalone fork is already installed and you want to
switch to OCA's `queue_job` without uninstalling anything.

> **This is an advanced operation.  Test on a staging environment first.**
>
> - **Back up your database** (including the filestore) before starting.
> - **Drain or cancel all pending jobs** before the upgrade.  Jobs in a
>   non-complete state may not survive if there are any schema differences
>   between the standalone fork and OCA's module.
> - **Install `queue_job` before upgrading** the bridge.  Odoo will not
>   resolve the bridge's new dependency automatically during upgrade — if
>   `queue_job` is absent the upgrade will fail.

**Steps**

1. **Install OCA's `queue_job`.**

   From the Apps menu, install the OCA *Job Queue* module.  At this point both
   the standalone `integration_queue_job` and OCA's `queue_job` are active —
   this is temporary and safe.

2. **Replace the standalone module files with the bridge.**

   On the filesystem, replace the contents of your existing
   `integration_queue_job` add-on directory with the contents of
   `integration_queue_job_bridge` (keeping the directory name
   `integration_queue_job`):

   ```bash
   rm -rf /path/to/your/addons/integration_queue_job
   cp -r integration_queue_job_bridge /path/to/your/addons/integration_queue_job
   ```

3. **Upgrade `integration_queue_job`.**

   Run the upgrade via the command line for full visibility over any errors:

   ```bash
   odoo-bin -u integration_queue_job -d <your_database>
   ```

4. **Verify connectors.**

   Confirm that all VentorTech connector modules are still installed and
   functioning.  No changes to their code are required.

### What the bridge does internally

The bridge's `post_init_hook` creates `ir.model.data` alias records:

| Alias XML ID                                    | Points to                           |
| ----------------------------------------------- | ----------------------------------- |
| `integration_queue_job.channel_root`            | `queue_job.channel_root`            |
| `integration_queue_job.group_queue_job_manager` | `queue_job.group_queue_job_manager` |

These aliases make every XML `ref=`, `groups=`, and Python `env.ref()` call
that uses the `integration_queue_job.*` prefix resolve to the correct records
owned by OCA's module — transparently and without touching any connector code.

---

## License

LGPL-3.0 or later — see individual file headers for full copyright notices.
