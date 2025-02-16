class AppContext:
    _settings_manager = None
    _json_manager = None
    _special_placement_handler = None

    @classmethod
    def init(cls, settings_manager, json_manager, special_placement_handler):
        cls._settings_manager = settings_manager
        cls._json_manager = json_manager
        cls._special_placement_handler = special_placement_handler

    @classmethod
    def settings_manager(cls):
        if cls._settings_manager is None:
            raise RuntimeError("AppContext.settings_manager() accessed before init()")
        return cls._settings_manager

    @classmethod
    def json_manager(cls):
        if cls._json_manager is None:
            raise RuntimeError("AppContext.json_manager() accessed before init()")
        return cls._json_manager

    @classmethod
    def special_placement_handler(cls):
        if cls._special_placement_handler is None:
            raise RuntimeError(
                "AppContext.special_placement_handler() accessed before init()"
            )
        return cls._special_placement_handler
