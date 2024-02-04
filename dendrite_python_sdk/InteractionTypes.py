class InteractionTypes:
    CLICK = "click"
    SEND_KEYS = "send_keys"
    PRESS_ENTER = "press_enter"

    @staticmethod
    def is_valid_interaction_type(type):
        return type in vars(InteractionTypes).values()

    @staticmethod
    def get_valid_interaction_types():
        return [
            value
            for name, value in vars(InteractionTypes).items()
            if not name.startswith("_")
            and not callable(value)
            and isinstance(value, str)
        ]
