from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Any, Protocol


class Clock(Protocol):
  def now_ns(self) -> int: ...


@dataclass(frozen=True, order=True)
class DelayedFrame:
  release_ns: int
  sequence: int
  source_frame_id: int
  capture_ns: int
  payload: Any


class DelayQueue:
  """Pure scheduling primitive used to test the production queue contract."""

  def __init__(self, clock: Clock, capacity_frames: int):
    if capacity_frames < 1:
      raise ValueError("capacity_frames must be positive")
    self.clock = clock
    self.capacity_frames = capacity_frames
    self._sequence = 0
    self._frames: list[DelayedFrame] = []

  def push(self, source_frame_id: int, capture_ns: int, payload: Any, delay_ms: int) -> bool:
    if delay_ms < 0:
      raise ValueError("delay_ms must be non-negative")
    if len(self._frames) >= self.capacity_frames:
      return False
    frame = DelayedFrame(capture_ns + delay_ms * 1_000_000, self._sequence, source_frame_id, capture_ns, payload)
    self._sequence += 1
    heapq.heappush(self._frames, frame)
    return True

  def pop_ready(self) -> list[DelayedFrame]:
    ready: list[DelayedFrame] = []
    while self._frames and self._frames[0].release_ns <= self.clock.now_ns():
      ready.append(heapq.heappop(self._frames))
    return ready

  def close(self) -> None:
    self._frames.clear()

  @property
  def depth(self) -> int:
    return len(self._frames)
