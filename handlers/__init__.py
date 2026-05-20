def register_handlers(bot):
    from .private_handler import register_private_handlers
    register_private_handlers(bot)

    from .group_handler import register_group_handlers
    register_group_handlers(bot)
    
    from .rules_handler import register_rules_handlers
    register_rules_handlers(bot)
    
    print("Handlers registered")

