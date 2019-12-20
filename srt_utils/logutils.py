# https://stash.haivision.com/projects/SSRT/repos/srthub-api/browse/test/e2e/lib/srthub_api_e2e/logutils.py?at=refs%2Fheads%2Fdev
import logging


class ContextualLoggerAdapter(logging.LoggerAdapter):
    """
    A simple Logger wrapper for conveniently adding extra context
    to messages.

    It will prepend messages with the 'context' string provided
    in the 'extra' dictionary, for example::

        LOGGER = logging.getLogger(__name__)
        ctxlog = ContextualLoggerAdapter(
            LOGGER,
            {'context': 'MyComponent'},
        )
        ctxlog.error('something broke')

    The resulting log message would be ``'MyComponent: something broke'``.
    """
    def process(self, msg, kwargs):
        ctx = self.extra['context']
        return  f"{ctx}: {msg}", kwargs