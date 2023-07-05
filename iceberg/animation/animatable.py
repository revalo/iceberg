from typing import Sequence, Union

from abc import ABC, abstractproperty, abstractmethod
import numpy as np


class Animatable(ABC):
    @abstractproperty
    def animatables(self) -> "AnimatableSequence":
        """Should return a sequence of sub-objects that can be animated."""
        pass

    @abstractmethod
    def copy_with_animatables(self, animatables: "AnimatableSequence"):
        """Should return a copy of the object with the animatable scalars set to the specified
        values.
        """
        pass

    def copy_with_animatable_vector(self, animatable_vector: np.ndarray):
        """Should return a copy of the object with the animatable scalars set to the specified
        values.
        """

        animatables = self.animatables

        cursor = 0
        new_animatables = []
        for animatable in animatables:
            if animatable is None:
                new_animatables.append(None)
                continue

            if isinstance(animatable, Animatable):
                placeholder_vector = animatable.animatables_to_vector()
            elif isinstance(animatable, np.ndarray):
                placeholder_vector = animatable
            elif isinstance(animatable, float) or isinstance(animatable, int):
                placeholder_vector = np.array([animatable])
            else:
                # Skip.
                continue

            current_vector = animatable_vector[
                cursor : cursor + len(placeholder_vector)
            ]
            cursor += len(placeholder_vector)

            if isinstance(animatable, Animatable):
                new_animatable = animatable.copy_with_animatable_vector(current_vector)
            elif isinstance(animatable, np.ndarray):
                new_animatable = current_vector
            else:
                new_animatable = current_vector[0]

            new_animatables.append(new_animatable)

        return self.copy_with_animatables(new_animatables)

    def animatables_to_vector(self) -> np.ndarray:
        """Return the animatable vector for this object.

        Recursively calls `animatables` on all sub-objects.
        """

        animatables = self.animatables

        if len(animatables) == 0:
            return np.array([])

        animatable_vectors = []
        for animatable in animatables:
            if isinstance(animatable, Animatable):
                animatable_vectors.append(animatable.animatables_to_vector())
            elif isinstance(animatable, np.ndarray):
                animatable_vectors.append(animatable)
            elif isinstance(animatable, float) or isinstance(animatable, int):
                animatable_vectors.append(np.array([animatable]))
            else:
                # Skip.
                pass

        return np.concatenate(animatable_vectors)


AnimatableSequence = Sequence[Union[float, np.ndarray, Animatable, None]]
