class EventBus:
    _listeners = {}
    
    @classmethod
    def emit(cls, event_name: str, data=None):
        """Emitir evento"""
        if event_name in cls._listeners:
            for callback in cls._listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[EventBus] Erro no callback: {e}")
    
    @classmethod
    def on(cls, event_name: str, callback):
        """Registrar listener"""
        if event_name not in cls._listeners:
            cls._listeners[event_name] = []
        cls._listeners[event_name].append(callback)
    
    @classmethod
    def off(cls, event_name: str, callback=None):
        """Remover listener"""
        if event_name in cls._listeners:
            if callback:
                if callback in cls._listeners[event_name]:
                    cls._listeners[event_name].remove(callback)
            else:
                cls._listeners[event_name].clear()