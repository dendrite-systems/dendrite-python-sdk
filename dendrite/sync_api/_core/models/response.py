from typing import Dict, Iterator
from dendrite.sync_api._core.dendrite_element import Element


class ElementsResponse:
    """
    ElementsResponse is a class that encapsulates a dictionary of Dendrite elements,
    allowing for attribute-style access and other convenient interactions.

    This class is used to store and access the elements retrieved by the `get_elements` function.
    The attributes of this class dynamically match the keys of the dictionary passed to the `get_elements` function,
    allowing for direct attribute-style access to the corresponding `Element` objects.

    Attributes:
        _data (Dict[str, Element]): A dictionary where keys are the names of elements and values are the corresponding `Element` objects.

    Args:
        data (Dict[str, Element]): The dictionary of elements to be encapsulated by the class.

    Methods:
        __getattr__(name: str) -> Element:
            Allows attribute-style access to the elements in the dictionary.

        __getitem__(key: str) -> Element:
            Enables dictionary-style access to the elements.

        __iter__() -> Iterator[str]:
            Provides an iterator over the keys in the dictionary.

        __repr__() -> str:
            Returns a string representation of the class instance.
    """

    _data: Dict[str, Element]

    def __init__(self, data: Dict[str, Element]):
        self._data = data

    def __getattr__(self, name: str) -> Element:
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __getitem__(self, key: str) -> Element:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._data})"
