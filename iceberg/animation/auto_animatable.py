import inspect
import functools
import numpy as np

from .animatable import Animatable, AnimatableSequence


def is_animatable(obj):
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
    if isinstance(obj, (float, np.ndarray, Animatable, int)) or obj is None:
        return obj
    if isinstance(obj, (list, tuple)):
        return np.array(obj).reshape(-1)

    raise ValueError(f"Object {obj} is not animatable")


def auto_animatable(cls):
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
        animatable_dict = {
            key: as_animatable(self._init_kwargs[key]) for key in self._animatable_keys
        }
        if hasattr(self, "_transform_export_animatable_dict"):
            animatable_dict = self._transform_export_animatable_dict(animatable_dict)
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
