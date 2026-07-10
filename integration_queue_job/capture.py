"""Capture stdout, stderr, and root-logger output for one block of code.

Wrap any callable section with :func:`capture_output`. Everything that would
normally go to the process stdout/stderr or through the root logger is copied
into an in-memory string buffer. When the block ends, read the result with
``buf.getvalue()`` and use it however you need (persist, return, inspect).

How it works:

1. A single :class:`StringIO` buffer is created for the ``with`` block.
2. ``sys.stdout`` and ``sys.stderr`` are replaced with :class:`_Tee` objects
   that write to both the original streams and the buffer (live output is
   unchanged).
3. A temporary :class:`_BufferHandler` is attached to Python's *root* logger
   so log records are formatted and appended to the same buffer.
4. On exit (success or exception), streams, logger level, and handler are
   restored; the buffer remains available to the caller via ``yield``.

The :data:`_buffer` context variable ties the logging handler to the active
buffer so nested or concurrent ``capture_output()`` calls stay isolated.
"""

import logging
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from io import StringIO
from typing import Iterator, TextIO


# Buffer for the innermost active ``capture_output()`` context.
# The logging handler reads this on each record instead of holding a buffer
# reference directly, which keeps nested captures correct.
_buffer: ContextVar[StringIO | None] = ContextVar("capture_output_buffer", default=None)


class _BufferHandler(logging.Handler):
    """Append formatted log records to the buffer for the active capture context.

    Registered on the root logger only while :func:`capture_output` runs.
    Each :meth:`emit` resolves the target buffer from :data:`_buffer`. If no
    capture is active, records are discarded by this handler.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Write one formatted log line into the active capture buffer.

        Invoked by the logging framework for each record delivered to this
        handler. No-op when :data:`_buffer` is unset.
        """
        buf = _buffer.get()
        if buf is not None:
            buf.write(self.format(record) + "\n")


class _Tee:
    """Duplicate writes to an original text stream and a capture buffer.

    Substitutes for ``sys.stdout`` or ``sys.stderr`` during capture so
    callers still see normal terminal output while a copy is retained in memory.
    """

    def __init__(self, original: TextIO, buffer: StringIO) -> None:
        """Pair a live stream with the in-memory capture target.

        :param original: Stream being wrapped (typically process stdout or stderr).
        :param buffer: :class:`StringIO` that accumulates a copy of all writes.
        """
        self._original = original
        self._buffer = buffer

    def write(self, data: str) -> int:
        """Forward ``data`` to the original stream and to the capture buffer.

        :returns: Length of ``data``, matching standard :class:`TextIO` behavior.
        """
        self._original.write(data)
        self._buffer.write(data)
        return len(data)

    def flush(self) -> None:
        """Flush the underlying original stream only."""
        self._original.flush()


@contextmanager
def capture_output() -> Iterator[StringIO]:
    """Collect stdout, stderr, and root-logger output for the ``with`` block.

    Example::

        with capture_output() as buf:
            print("step one")
            logger.info("step two")
        transcript = buf.getvalue()

    Inside the block:

    - Writes to stdout/stderr are teed: originals still receive data, and a
      copy is stored in the yielded buffer.
    - Records reaching the root logger at DEBUG or lower are formatted
      (timestamp, level, logger name, message) and appended to that buffer.

    Teardown always runs (including on exceptions): process streams and root
    logger configuration are restored. The buffer content is preserved for use
    after the block or in a ``finally`` clause.

    :yields: Shared :class:`StringIO` for the capture session; call
        :meth:`~io.StringIO.getvalue` to obtain the full text.
    """
    buffer = StringIO()
    token = _buffer.set(buffer)

    handler = _BufferHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    old_level = root_logger.level
    root_logger.addHandler(handler)
    if root_logger.level > logging.DEBUG:
        root_logger.setLevel(logging.DEBUG)

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = _Tee(old_stdout, buffer)  # type: ignore[assignment]
    sys.stderr = _Tee(old_stderr, buffer)  # type: ignore[assignment]

    try:
        yield buffer
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)
        _buffer.reset(token)
