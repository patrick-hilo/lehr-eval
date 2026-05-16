from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from lehr_eval.db import connect


Event = dict[str, Any]


@dataclass(frozen=True)
class EventTarget:
    evaluation_id: int
    phase: str
    item: int | None


@dataclass(frozen=True)
class _Subscriber:
    queue: asyncio.Queue[Event]
    loop: asyncio.AbstractEventLoop | None


class EventSubscription:
    def __init__(self, hub: EventHub, evaluation_id: int, subscriber: _Subscriber):
        self._hub = hub
        self._evaluation_id = evaluation_id
        self._subscriber = subscriber
        self._closed = False

    def __aiter__(self) -> EventSubscription:
        return self

    async def __anext__(self) -> Event:
        if self._closed:
            raise StopAsyncIteration
        return await self._subscriber.queue.get()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._hub.unsubscribe(self._evaluation_id, self._subscriber)


class EventHub:
    def __init__(self) -> None:
        self._subscribers: dict[int, set[_Subscriber]] = defaultdict(set)

    def subscribe(self, evaluation_id: int) -> EventSubscription:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        subscriber = _Subscriber(queue=asyncio.Queue(), loop=loop)
        self._subscribers[evaluation_id].add(subscriber)
        return EventSubscription(self, evaluation_id, subscriber)

    def unsubscribe(self, evaluation_id: int, subscriber: _Subscriber) -> None:
        subscribers = self._subscribers.get(evaluation_id)
        if subscribers is None:
            return
        subscribers.discard(subscriber)
        if not subscribers:
            del self._subscribers[evaluation_id]

    async def publish(self, evaluation_id: int, event: Event) -> None:
        self.publish_nowait(evaluation_id, event)

    def publish_nowait(self, evaluation_id: int, event: Event) -> None:
        for subscriber in list(self._subscribers.get(evaluation_id, ())):
            self._deliver(subscriber, dict(event))

    def _deliver(self, subscriber: _Subscriber, event: Event) -> None:
        if subscriber.loop is None or not subscriber.loop.is_running():
            subscriber.queue.put_nowait(event)
            return

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is subscriber.loop:
            subscriber.queue.put_nowait(event)
        else:
            subscriber.loop.call_soon_threadsafe(subscriber.queue.put_nowait, event)


def create_events_router(db_path: Path, hub: EventHub) -> APIRouter:
    router = APIRouter()

    @router.get("/events/{evaluation_token}")
    async def events(request: Request, evaluation_token: str) -> StreamingResponse:
        evaluation_id = evaluation_id_for_token(db_path, evaluation_token)
        subscription = hub.subscribe(evaluation_id)
        target = event_target_for_evaluation(db_path, evaluation_id)

        async def stream() -> AsyncIterator[str]:
            try:
                yield sse_data(
                    {"phase": target.phase, "item": target.item, "snapshot": True}
                )
                async for event in subscription:
                    if await request.is_disconnected():
                        break
                    yield sse_data(event)
            finally:
                subscription.close()

        return StreamingResponse(stream(), media_type="text/event-stream")

    return router


def evaluation_id_for_token(db_path: Path, evaluation_token: str) -> int:
    with connect(db_path) as db:
        row = db.execute(
            """
            select id
            from evaluations
            where student_token = ? or teacher_token = ?
            """,
            (evaluation_token, evaluation_token),
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return int(row["id"])


def event_target_for_evaluation(db_path: Path, evaluation_id: int) -> EventTarget:
    with connect(db_path) as db:
        row = db.execute(
            """
            select id, status, current_item_index
            from evaluations
            where id = ?
            """,
            (evaluation_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    item = row["current_item_index"]
    return EventTarget(
        evaluation_id=int(row["id"]),
        phase=row["status"],
        item=None if item is None else int(item),
    )


def sse_data(event: Event) -> str:
    return f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
