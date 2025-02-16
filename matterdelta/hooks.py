"""Event Hooks"""
import logging
from argparse import Namespace

from deltabot_cli import AttrDict, Bot, BotCli, EventType, const, events

from .api import dc2mb, init_api
from .util import get_log_level

cli = BotCli("matterdelta", log_level=get_log_level())


@cli.on_init
async def _on_init(bot: Bot, _args: Namespace) -> None:
    if not await bot.account.get_config("displayname"):
        await bot.account.set_config("displayname", "Matterbridge Bot")
        status = "I am a Delta Chat bot, send me /help for more info"
        await bot.account.set_config("selfstatus", status)


@cli.on_start
async def _on_start(bot: Bot, args: Namespace) -> None:
    system_info = await bot.account.manager.get_system_info()
    addr = await bot.account.get_config("addr")
    logging.info(
        "Delta Chat %s listening at: %s", system_info.deltachat_core_version, addr
    )

    await init_api(bot, args.config_dir)


@cli.on(events.RawEvent)
async def _log_event(event: AttrDict) -> None:
    if event.type == EventType.INFO:
        logging.info(event.msg)
    elif event.type == EventType.WARNING:
        logging.warning(event.msg)
    elif event.type == EventType.ERROR:
        logging.error(event.msg)


@cli.on(events.NewMessage(command="/id"))
async def _id(event: AttrDict) -> None:
    msg = event.message_snapshot
    chat = await msg.chat.get_basic_snapshot()
    if chat.chat_type == const.ChatType.SINGLE:
        await msg.chat.send_message(
            text="Can't use /id command here, add me to a group and use the command there",
            quoted_msg=msg.id,
        )
    else:
        await msg.chat.send_text(str(msg.chat_id))


@cli.on(events.NewMessage(is_info=False, is_bot=None, func=cli.is_not_known_command))
async def _bridge(event: AttrDict) -> None:
    msg = event.message_snapshot
    chat = await msg.chat.get_basic_snapshot()
    if chat.chat_type == const.ChatType.SINGLE and not msg.is_bot:
        text = (
            "**Available commands**\n\n"
            "/id - send me this command in a group to get its chatId."
        )
        await msg.chat.send_text(text)
    else:
        await dc2mb(msg)
