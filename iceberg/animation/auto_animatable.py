import inspect
import functools
import numpy as np

from .animatable import Animatable, AnimatableSequence


def is_animatable(obj):
    """Check whether `obj` can be animated."""
    if isinstance(obj, (Animatable, np.ndarray, float, int)):
        return True
    if obj is None:
        return True
    if isinstance(obj, (list, tuple)):
        # In addition to Animatables, we allow lists of floats,
        # or lists of lists/tuples of floats, since some iceberg classes accept
        # these instead of numpy arrays.
        if all(isinstance(item, (float, int)) for item in obj):
            return True
        if all(
            isinstance(item, (tuple, list, np.ndarray))
            and len(item) == len(obj[0])
            and all(isinstance(subitem, (float, int)) for subitem in item)
            for item in obj
        ):
            return True
    return False


def as_animatable(obj):
    """Try to turn `obj` into something to be returned by `Animatable.animatables`."""
    if isinstance(obj, (Animatable, float, int)) or obj is None:
        return obj
    if isinstance(np.ndarray, obj):
        return obj.reshape(-1)
    if isinstance(obj, (list, tuple)):
        return np.array(obj).reshape(-1)

    raise ValueError(f"Object {obj} is not animatable")


def auto_animatable(cls):
    """Class decorator that makes a class Animatable.

    Usage:
        @auto_animatable
        class MyClass(Drawable):
            ...

    This will try to automatically capture all the arguments passed to __init__,
    detect which of them are animatable, and then add suitable `animatables` and
    `copy_with_animatables` methods.

    Note that `MyClass` mustn't explicitly inherit from `Animatable`---this would lead
    to errors as `MyClass` wouldn't have the necessary abstract methods defined.
    Instead, the decorator will add `Animatable` as a parent class. (Technically,
    it returns a new class that inherits from `MyClass` and `Animatable`.)

    You can modify the animatables by defining `_transform_export_animatable_dict`
    and/or `_transform_import_animatable_dict` methods on the class. Both take a dict
    where keys are names of animatable __init__ kwargs, and values are the __init__
    arguments. The methods can then return a modified dict.

    This decorator should work for many cases, but in complex scenarios, you will
    instead need to manually define `animatables` and `copy_with_animatables`.
    """
    orig_init = cls.__init__
    sig = inspect.signature(orig_init)

    @functools.wraps(cls.__init__)
    def new_init(self, *args, **kwargs):
        if hasattr(self, "_is_auto_animatable"):
            # This is the __init__ of a parent class, called from an auto_animatable
            # child class. No need to do anything here.
            orig_init(self, *args, **kwargs)
            return

        # Important to set this before calling orig_init!
        self._is_auto_animatable = True

        orig_init(self, *args, **kwargs)

        bound = sig.bind(self, *args, **kwargs)
        bound.apply_defaults()

        self._animatable_keys = []
        self._shapes = {}
        self._init_kwargs = {}
        for key, value in bound.arguments.items():
            if key == "self":
                continue

            self._init_kwargs[key] = value

            if is_animatable(value):
                self._animatable_keys.append(key)
                if isinstance(value, (np.ndarray, list, tuple)):
                    value = np.array(value)
                    self._shapes[key] = value.shape

    cls.__init__ = new_init

    @property
    def animatables(self) -> AnimatableSequence:
        if hasattr(self, "_transform_export_animatable_dict"):
            animatable_dict = self._transform_export_animatable_dict(animatable_dict)
        animatable_dict = {
            key: as_animatable(self._init_kwargs[key]) for key in self._animatable_keys
        }
        return tuple(animatable_dict.values())

    cls.animatables = animatables

    def copy_with_animatables(self, animatables: AnimatableSequence):
        animatable_dict = dict(zip(self._animatable_keys, animatables))
        for key, shape in self._shapes.items():
            value = animatable_dict[key]
            assert isinstance(value, np.ndarray)
            value = value.reshape(shape)
            animatable_dict[key] = value

        if hasattr(self, "_transform_import_animatable_dict"):
            animatable_dict = self._transform_import_animatable_dict(animatable_dict)

        kwargs = {**self._init_kwargs, **animatable_dict}
        # Need to use cls instead of self.__class__ because otherwise the init kwargs
        # might be wrong for classes that inherit from auto_animatable classes.
        # This does mean that Child.copy_with_animatables will return a Parent if not
        # overriden, but that's true throughout iceberg anyway.
        return cls(**kwargs)

    cls.copy_with_animatables = copy_with_animatables

    return type(cls.__name__, (cls, Animatable), {})
