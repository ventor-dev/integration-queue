=====================
Integration Queue Job
=====================

Overview
--------
The **Integration Queue Job** module is a lightweight fork of the OCA `queue_job` addon.
It provides background job processing for Odoo, optimized to work seamlessly with
VentorTech's e-commerce connectors (`https://ecosystem.ventor.tech/ <https://ecosystem.ventor.tech/>`_).

This fork keeps only the features needed for our connectors, simplifying the codebase
while remaining compatible with the original `queue_job`. You can safely use either
module with our connectors.

Why this fork?
--------------
- Focused and simplified job queue system (reduced complexity).
- Fully compatible with VentorTech e-commerce connectors.
- Preserves compatibility with the original OCA `queue_job`.
- Easier maintenance across Odoo versions.

Usage Example
-------------
You can postpone method calls to be executed asynchronously:

.. code:: python

   class MyModel(models.Model):
       _name = 'my.model'

       def my_method(self, a, k=None):
           _logger.info("executed with a=%s, k=%s", a, k)

   class MyOtherModel(models.Model):
       _name = 'my.other.model'

       def button_do_stuff(self):
           # This will run in the background
           self.env['my.model'].with_delay().my_method('a', k=2)

Release Notes
-------------
* 1.0.8 (2026-07-10)
    - Fixed the job runner re-dispatching the same job about once per second
      until the platform answered HTTP 429. ``/queue_job/runjob`` only responds
      once the job has finished, so the runner's 1 second timeout means "we are
      not waiting for the result", not "the request failed". Treating it as a
      failure reset the job to ``pending``, which notified the runner, which
      re-dispatched it, and so on. A timeout is now ignored. Jobs whose request
      really was lost are still recovered by the ``Jobs Garbage Collector`` cron.
    - The runner no longer resets a job to ``pending`` on arbitrary request
      exceptions either. It only postpones on HTTP 429, with the ``Retry-After``
      backoff introduced in 1.0.5.
    - Raised the ``Jobs Garbage Collector`` cron's ``started_delta`` from 15 to
      20 minutes. Odoo caps a request at ``limit_time_real`` (900s on Odoo.sh)
      but takes up to ~121s more to actually kill the thread, so a job could be
      requeued while it was still running and, since nothing locks a running job,
      executed a second time in parallel.

      **Action required on existing databases.** The cron is declared with
      ``noupdate="1"``, so upgrading the module does not change it. Open
      *Settings > Technical > Scheduled Actions > Jobs Garbage Collector* and set
      ``started_delta=20`` (or ``0`` to stop requeuing started jobs altogether).
      Fresh installs get the new value automatically.
    - ``queue_job_host`` / ``queue_job_port`` now fall back to Odoo's own
      ``http_interface`` / ``http_port`` when unset, instead of being pinned to
      ``localhost:8069``.
    - Fixed a file descriptor leak: the runner's stop-pipe is closed again.

* 1.0.7 (2026-07-10)
    - Removed the deprecated ``Request._get_session_and_dbname`` monkey patch
      (``post_load`` hook). The ``X-Odoo-Database`` header introduced in 1.0.6
      fully replaces it.

* 1.0.6 (2026-06-11)
    - Fixed job runner failing with "'NoneType' object is not callable" on
      multi-database instances. The runner now passes the target database in
      the ``X-Odoo-Database`` header so Odoo binds it during routing, instead
      of relying on auto-detection of a single database.

* 1.0.5 (2026-05-21)
    - Fixed job runner retry loop on HTTP 429 responses by postponing rate-limited jobs according to Retry-After.

* 1.0.4 (2026-13-02)
    - Added automatic requeuing of stuck jobs (5 min enqueued, 15 min started).

* 1.0.3 (2025-11-10)
    - Fixed create method to handle empty vals_list (Odoo tests compatibility).

* 1.0.2 (2025-10-28)
    - Fixed database lock issues.

* 1.0.1 (2025-09-23)
    - Small fixes and improvements.

* 1.0.0 (2025-09-16)
    - Initial release (forked from OCA/queue, cleaned up for VentorTech connectors).

Credits
-------
**Original Authors (queue_job):**
- Camptocamp
- ACSONE SA/NV
- Odoo Community Association (OCA)

**Maintained Fork (integration_queue_job):**
- VentorTech (https://ventor.tech)

License
-------
LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
