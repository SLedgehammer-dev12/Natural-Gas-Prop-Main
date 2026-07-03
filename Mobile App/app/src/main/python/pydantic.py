"""
Lightweight pydantic.py polyfill for Chaquopy on Android.
Eliminates the native Rust dependency 'pydantic-core' and speeds up application startup.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Union

class FieldInfo:
    def __init__(self, default=None, **kwargs):
        self.default = default
        self.metadata = kwargs

def Field(default=None, **kwargs):
    return FieldInfo(default, **kwargs)

def field_validator(*args, **kwargs):
    # Dummy decorator: does nothing on mobile side
    def decorator(func):
        return func
    return decorator

def computed_field(func):
    # Converts method to a standard property
    if isinstance(func, property):
        return func
    return property(func)

class ConfigDict(dict):
    """Dummy class to mock Pydantic V2 ConfigDict."""
    pass

class BaseModel:
    """Polyfill for Pydantic BaseModel with basic dict serialization and default assignment."""
    def __init__(self, **kwargs):
        # Set all values provided in kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        # Assign defaults for class-level variables (Fields) that weren't provided
        for name in dir(self.__class__):
            if name.startswith('_'):
                continue
            val = getattr(self.__class__, name)
            if isinstance(val, FieldInfo):
                if name not in kwargs:
                    # If it's a field with default, assign it
                    if val.default is not Ellipsis:
                        setattr(self, name, val.default)
                    else:
                        # Otherwise set to None
                        setattr(self, name, None)

    def validate_total(self, *args, **kwargs):
        # Specific custom validate_total defined in child class
        if hasattr(self, 'components'):
            pass

    def model_dump(self) -> Dict[str, Any]:
        return self.dict()

    def dict(self) -> Dict[str, Any]:
        result = {}
        # Serialize fields from instance variables
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = self._serialize_value(value)
                
        # Serialize computed properties (properties / computed_fields)
        for key in dir(self.__class__):
            if not key.startswith('_'):
                val = getattr(self.__class__, key)
                if isinstance(val, property):
                    try:
                        result[key] = self._serialize_value(getattr(self, key))
                    except Exception:
                        result[key] = None
                        
        return result

    def _serialize_value(self, val: Any) -> Any:
        if isinstance(val, BaseModel):
            return val.dict()
        elif isinstance(val, list):
            return [self._serialize_value(item) for item in val]
        elif isinstance(val, dict):
            return {k: self._serialize_value(v) for k, v in val.items()}
        return val
