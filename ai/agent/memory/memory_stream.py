from agent.memory.memory import Memory, BACKGROUND, PLAN
from typing import List, Dict

from utils.tools import get_idle_id

class MemoryStream:

    def __init__(self):
        self.stream = list()
        self.background = None
        self.plan = None

    def store_memory(self, new_memory: Memory):
        # redis.xadd(name=self.stream_name, fields=new_memory.__dict__)
        new_memory.set_id(get_idle_id(self.stream, 1, len(self.stream)))
        if new_memory.memory_type == BACKGROUND:
            self.background = new_memory
        else:
            self.stream.append(new_memory)
            if new_memory.memory_type == PLAN:
                self.plan = new_memory
    
    def complete_plan(self):
        for memory in self.stream:
            # diff = time_tick - memory.created
            if memory.id == self.plan.id:
                # memories.append(memory)
                memory.mark_completed()

    # def ready_to_reflect(self) -> bool:
    #     """
    #     Queries the memory store to determine if the importance score of
    #     the most recent memories exceeds a specific threshold.
    #     :return:
    #     """
    #     ...

    def most_recent_memories(self, time_tick: int, time_diff: int) -> List[Memory]:
        # retrieve memories from past day
        memories = list()
        for memory in self.stream:
            diff = time_tick - memory.created
            if diff <= time_diff:
                memories.append(memory)
                memory.last_access = time_tick
        return memories

    def get_similar_memory(self, query_memory: Memory, params: Dict[str, float], time_tick: int) -> List[Memory]:
        # Get related memories (memories with highest retrieval scores relative to query memory)
        # redis.xrange(name=self.stream_name)
        memories = list()
        for memory in self.stream:
            score = memory.retrieval_score(query_memory, params, time_tick)
            if score >= params["retrieval_score_threshold"]:
                memories.append(memory)
                memory.last_access = time_tick
        return memories
