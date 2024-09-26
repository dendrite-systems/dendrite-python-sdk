from typing import Any, Union, Literal
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk.async_api._exceptions.dendrite_exception import DendriteException


class KeyboardMixin(DendritePageProtocol):

    async def press(
        self,
        key: Union[
            str,
            Literal[
                "Enter",
                "Tab",
                "Escape",
                "Backspace",
                "ArrowUp",
                "ArrowDown",
                "ArrowLeft",
                "ArrowRight",
            ],
        ],
        hold_shift: bool = False,
        hold_ctrl: bool = False,
        hold_alt: bool = False,
        hold_cmd: bool = False,
    ):
        """
        Presses a keyboard key on the active page, optionally with modifier keys.

        Args:
            key (Union[str, Literal["Enter", "Tab", "Escape", "Backspace", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]]): The main key to be pressed.
            hold_shift (bool, optional): Whether to hold the Shift key. Defaults to False.
            hold_ctrl (bool, optional): Whether to hold the Control key. Defaults to False.
            hold_alt (bool, optional): Whether to hold the Alt key. Defaults to False.
            hold_cmd (bool, optional): Whether to hold the Command key (Meta on some systems). Defaults to False.

        Returns:
            Any: The result of the key press operation.

        Raises:
            DendriteException: If the key press operation fails.
        """
        modifiers = []
        if hold_shift:
            modifiers.append("Shift")
        if hold_ctrl:
            modifiers.append("Control")
        if hold_alt:
            modifiers.append("Alt")
        if hold_cmd:
            modifiers.append("Meta")

        if modifiers:
            key = "+".join(modifiers + [key])

        try:
            page = await self._get_page()
            await page.keyboard.press(key)
        except Exception as e:
            raise DendriteException(
                message=f"Failed to press key: {key}. Error: {str(e)}",
                screenshot_base64="",
            )
