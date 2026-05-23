from __future__ import annotations
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Type, TypeVar
import logging
from requirements.contracts.events import DomainEvent

T = TypeVar("T", bound=DomainEvent)
Handler = Callable[[DomainEvent], None]
logger = logging.getLogger(__name__)


class IEventBus(ABC):
    @abstractmethod
    def subscribe(self, event_type: Type[T], handler: Handler) -> None: ...

    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...


class InProcessEventBus(IEventBus):
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[T], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error(
                    f"Handler {handler.__qualname__} falhou para "
                    f"{type(event).__name__} [{event.event_id}]: {exc}",
                    exc_info=True,
                )
