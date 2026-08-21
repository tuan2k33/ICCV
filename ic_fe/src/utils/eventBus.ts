export enum EventBusType {
  SELECTED_COUNTER = 'SELECTED_COUNTER',
  SELECTED_AUDITOR = 'SELECTED_AUDITOR',
  DELETE_ALL_USER_REQUEST = 'DELETE_ALL_USER_REQUEST',
  CANCEL_DELETE_USER = 'CANCEL_DELETE_USER',
  CONFIRM_DELETE_USER = 'CONFIRM_DELETE_USER',
  START_DELETE_USER = 'START_DELETE_USER',
  STOP_DELETE_USER = 'STOP_DELETE_USER',
  CLEAR_SELECTED_USER = 'CLEAR_SELECTED_USER',
}

type EventListener<T> = (payload?: T) => void
type Store = Record<string, EventListener<any>[]>

class EventBus {
  private store: Store = {}

  public on<T>(event: EventBusType | string, listener: EventListener<T>) {
    if (!this.store[event]) this.store[event] = []
    this.store[event].push(listener as EventListener<any>)
  }
  public off(event: EventBusType | string, listener: EventListener<any>) {
    if (!this.store[event]) return
    this.store[event] = this.store[event].filter((_listener) => _listener !== listener)
  }

  public emit<T>(event: EventBusType | string, payload?: T) {
    this.store[event]?.forEach((listener) => (listener as EventListener<T>)(payload))
  }
}

export const eventBus = new EventBus()
