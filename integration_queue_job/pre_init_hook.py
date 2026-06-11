# Copyright 2025 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""
register_queue_process_func
============================

Inputs: p_pid, p_expiration_secs
threshold = p_expiration_secs / 4

+---------------------------------------+
|   Inputs: p_pid, p_expiration_secs    |
+---------------------------------------+
                    |
                    v
+---------------------------------------+
|  1. DELETE expired rows               |
|     WHERE expires_at < NOW()          |
+---------------------------------------+
                    |
                    v
+---------------------------------------+
|  2. SELECT main_pid                   |
|     WHERE is_main = TRUE LIMIT 1      |
|  3. SELECT remaining_time             |
|     expires_at - NOW() for p_pid      |
+---------------------------------------+
                    |
                    v
          +------------------+
          |  main_pid        |
          |  IS NULL?        |
          +--------+---------+
           Yes     |     No
       +-----------+-----------+
       v                       v
+---------------+     +----------------------+
| 4. Become     |     |  remaining_time      |
|    MAIN       |     |  IS NULL?            |
|  INSERT/UPSERT|     +----------+-----------+
|  is_main=TRUE |        Yes     |     No
|  expires_at = |    +-----------+-----------+
|  NOW + lease  |    v                       v
+-------+-------+ +-------------+   +--------------------+
        |         | 5a. INSERT  |   |  remaining_time    |
        |         | is_main=    |   |  < threshold?      |
        |         | FALSE       |   +----------+---------+
        |         +------+------+      Yes     |     No
        |                |          +----------+---------+
        |                |          v                    v
        |                |   +------------+    +-----------+
        |                |   | 5b. UPDATE |    | 5c. SKIP  |
        |                |   | expires_at |    | no write  |
        |                |   +-----+------+    +-----+-----+
        +----------------+---------+-----------------+
                                   |
                                   v
                    +--------------------------+
                    | 6. RETURN is_main        |
                    |    for p_pid (BOOLEAN)   |
                    +--------------------------+

Legend
------
TRUE  = this process is the main runner
FALSE = secondary runner (main already exists)

Become MAIN  : no active main -> this PID gets is_main = TRUE
INSERT FALSE : main exists, this PID is new -> secondary runner
UPDATE       : row exists and < 25% of lease left -> renew heartbeat
SKIP         : row exists with enough time left -> no DB write
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    _logger.info("Create an active_integration_queue_job_runner table")

    env.cr.execute("""
CREATE TABLE IF NOT EXISTS active_integration_queue_job_runner (
    pid TEXT PRIMARY KEY,
    is_main BOOLEAN NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS active_integration_queue_job_runner_expires_at_idx
    ON active_integration_queue_job_runner (expires_at);

CREATE UNIQUE INDEX IF NOT EXISTS active_integration_queue_job_runner_unique_main
    ON active_integration_queue_job_runner (is_main)
    WHERE is_main;
    """)

    _logger.info("Create a register_queue_process_func postgres function")

    env.cr.execute("""
CREATE OR REPLACE FUNCTION register_queue_process_func(
    p_pid TEXT,
    p_expiration_secs INT
)
RETURNS BOOLEAN
AS $$
DECLARE
    main_pid TEXT;
    remaining_time INTERVAL;
    threshold INTERVAL := INTERVAL '1 second' * (p_expiration_secs / 4);
BEGIN
    -- 1. Removing expired entries
    DELETE FROM active_integration_queue_job_runner
     WHERE expires_at < NOW();

    -- 2. Checking the current main process
    SELECT pid
      INTO main_pid
      FROM active_integration_queue_job_runner
     WHERE is_main = TRUE
     LIMIT 1;

    -- 3. Check if the process already exists in the table
    SELECT expires_at - NOW()
      INTO remaining_time
      FROM active_integration_queue_job_runner
     WHERE pid = p_pid;

    IF main_pid IS NULL THEN
        -- 4. If there is no main process, the current process becomes the main
        INSERT INTO active_integration_queue_job_runner (
            pid, is_main, expires_at
        )
        VALUES (
            p_pid,
            TRUE,
            NOW() + INTERVAL '1 second' * p_expiration_secs
        )
        ON CONFLICT (pid) DO UPDATE
        SET expires_at = EXCLUDED.expires_at,
            is_main = TRUE;
    ELSE
        -- 5. If the process already exists, update the expires_at only if less than 0.25*time left
        IF remaining_time IS NULL THEN
            -- There is no process -> create a new entry
            INSERT INTO active_integration_queue_job_runner (
                pid, is_main, expires_at
            )
            VALUES (
                p_pid,
                FALSE,
                NOW() + INTERVAL '1 second' * p_expiration_secs
            );
        ELSIF remaining_time < threshold THEN
            -- A little time left -> update the expires_at
            UPDATE active_integration_queue_job_runner
               SET expires_at = NOW() + INTERVAL '1 second' * p_expiration_secs
             WHERE pid = p_pid;
        END IF;
    END IF;

    -- 6. Return TRUE if the current process is the main one
    RETURN (
        SELECT is_main
          FROM active_integration_queue_job_runner
         WHERE pid = p_pid
    );
END;
$$ LANGUAGE plpgsql;
    """)
