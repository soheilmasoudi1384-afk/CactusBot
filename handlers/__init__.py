def register_handlers(bot):
    from .private_handler import register_private_handlers
    register_private_handlers(bot)

    from .group_handler import register_group_handlers
    register_group_handlers(bot)
    print("Handlers registered")
