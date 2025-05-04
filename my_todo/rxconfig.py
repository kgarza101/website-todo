import reflex as rx

config = rx.Config(
    app_name="my_todo",
    db_url="sqlite:///todo.db",
    env=rx.Env.DEV,
) 