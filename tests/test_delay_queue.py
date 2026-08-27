from simlab.delay_queue import DelayQueue


class FakeClock:
  def __init__(self): self.value = 0
  def now_ns(self): return self.value


def test_fifo_same_deadline_and_timestamp_preservation():
  clock = FakeClock(); queue = DelayQueue(clock, capacity_frames=3)
  assert queue.push(10, 0, "a", 50) and queue.push(11, 0, "b", 50)
  clock.value = 50_000_000
  ready = queue.pop_ready()
  assert [frame.source_frame_id for frame in ready] == [10, 11]
  assert [frame.capture_ns for frame in ready] == [0, 0]


def test_zero_delay_overflow_and_shutdown():
  clock = FakeClock(); queue = DelayQueue(clock, capacity_frames=1)
  assert queue.push(1, 7, "frame", 0) and not queue.push(2, 8, "overflow", 0)
  clock.value = 7
  assert queue.pop_ready()[0].payload == "frame"
  assert queue.push(3, 9, "pending", 100)
  queue.close(); assert queue.depth == 0
