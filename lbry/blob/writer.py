import typing
import logging
import asyncio
from io import BytesIO
from lbry.error import InvalidBlobHashError, InvalidDataError
from lbry.utils import get_lbry_hash_obj

log = logging.getLogger(__name__)


class HashBlobWriter:
    def __init__(self, expected_blob_hash: str, get_length: typing.Callable[[], int],
                 finished: asyncio.Future):
        self.expected_blob_hash = expected_blob_hash
        self.get_length = get_length
        self.buffer = BytesIO()
        self.finished = finished
        self.finished.add_done_callback(lambda *_: self.close_handle())
        self._hashsum = get_lbry_hash_obj()
        self.len_so_far = 0

    def __del__(self):
        if self.buffer is not None:
            log.warning("Garbage collection was called, but writer was not closed yet")
            self.close_handle()

    def calculate_blob_hash(self) -> str:
        return self._hashsum.hexdigest()

    def closed(self):
        return self.buffer is None or self.buffer.closed

    def write(self, data: bytes):
        expected_length = self.get_length()
        if not expected_length:
            raise OSError("unknown blob length")
        if self.buffer is None:
            log.warning("writer has already been closed")
            if not self.finished.done():
                self.finished.cancel()
                return
            raise OSError('I/O operation on closed file')

        self._hashsum.update(data)
        self.len_so_far += len(data)
        if self.len_so_far > expected_length:
            self.finished.set_exception(InvalidDataError(
                f'Length so far is greater than the expected length. {self.len_so_far} to {expected_length}'
            ))
            self.close_handle()
            return
        self.buffer.write(data)
        if self.len_so_far == expected_length:
            blob_hash = self.calculate_blob_hash()
            if blob_hash != self.expected_blob_hash:
                self.finished.set_exception(InvalidBlobHashError(
                    f"blob hash is {blob_hash} vs expected {self.expected_blob_hash}"
                ))
            elif self.finished and not (self.finished.done() or self.finished.cancelled()):
                self.finished.set_result(self.buffer.getvalue())
            self.close_handle()

    def close_handle(self):
        if not self.finished.done():
            self.finished.cancel()
        if self.buffer is not None:
            self.buffer.close()
            self.buffer = None
