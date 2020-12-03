import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "İstifadəçi qrupun yiyəsidir.",
    "Qrup tapılmadı",
    "Ban vermək üçün yetərli haqq yoxdur.",
    "İstifadəçi tapılmadı.",
    "İstifadəçi ID tapılmadı",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RUNBAN_ERRORS = {
    "İstifadəçi qrupun yiyəsidir.",
    "Qrup tapılmadı",
    "Ban vermək üçün yetərli haqq yoxdur.",
    "İstifadəçi tapılmadı.",
    "İstifadəçi ID tapılmadı",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir istifadəçini seçməmisiniz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Kaş adminləri ban edə biləcək super güclərim olsa...")
        return ""

    if user_id == bot.id:
        message.reply_text("Ha ha ha çox gülməlidi. Mən özümü ban etməyəcəm!")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} ban olundu!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Ban olundu!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir istifadəçini seçməmisiniz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Kaş adminləri ban edə biləcək super güclərim olsa...")
        return ""

    if user_id == bot.id:
        message.reply_text("Ha ha ha çox gülməlidi. Mən özümü ban etməyəcəm!")
        return ""

    if not reason:
        message.reply_text("Bu istifadəçini qadağan edəcək bir vaxt təyin etməmisiniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Ban olundu! Səbəb {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Ban olundu! Səbəb {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Adminləri çıxara biləcək qədər gücüm yoxdu.")
        return ""

    if user_id == bot.id:
        message.reply_text("Əlbəttə bunu etmiyəcəm...")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Lənət olsun, bu istifadəçini kick edə bilmirəm.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Admin olmadan bunu eləmək fikirin var?")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Problem yoxdu")
    else:
        update.effective_message.reply_text("Bacarmıram :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Biraz ciddi ol ha ha ha! Özüm özümü unban edim? ")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Niyə sərbəst birini unban edirsən ki?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Artıq qoşula bilər")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Görünür söhbət və ya istifadəçi haqqında danışmırsız.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir istifadəçini seçməmisiniz.")
        return
    elif not chat_id:
        message.reply_text("Bir söhbəti seçməmisiniz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Mən üzgünəm( Bu qrup gizlidi.")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("İstifadəçiləri bloklaya bilmirəm. Admin olduğumdan və istifadəçiləri qadağa etmə özəlliyimin açıq olduğuna fikir ver)")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Kaş adminləri ban edə biləcək super güclərim olsa...")
        return

    if user_id == bot.id:
        message.reply_text("Ha ha ha çox gülməlidi. Mən özümü ban etməyəcəm!")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Ban olundu!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Lənət olsun. Bu istifadəçini qadağa edə bilmirəm")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Görünür söhbət və ya istifadəçi haqqında danışmırsız.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir istifadəçini seçməmisiniz.")
        return
    elif not chat_id:
        message.reply_text("Görünür söhbət və ya istifadəçi haqqında danışmırsız..")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Qeyd qrup tapılmadı")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Qrup gizli olduğu üçün heçnə edə bilmərəm")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("İstifadəçiləri bloklaya bilmirəm. Admin olduğumdan və istifadəçiləri qadağa etmə özəlliyimin açıq olduğuna fikir ver)")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmirəm there")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Bu istifadəçinin onsuzda banı yoxdu. Banı olmayan istifadəçini necə unban edim? )")
        return

    if user_id == bot.id:
        message.reply_text("Bir bunu etmədiyin qalmışd)) Bunu etmiyəcəm çünki ADMİNƏM!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Uraa! Artıq istifadəçi qrupa qatıla bilər")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unban olundu!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Lənət olsun bu istifadəçinin qadağasın qaldıra bilmərəm.")


__help__ = """
 - /kickme: sizi olduğunuz qrupdan ban olunmadan atır.

*Admin only:*
 - /ban <istifadəçi adı/id>: istifadəçini ban edir. (mesajına cavab olaraq da yaza bilərsiz)
 - /tban <istifadəçi adı/id> x(m/h/d): bu istifadəçini x vaxta qədər ban edər. (mesajına cavab olaraq da yaza bilərsiz). m = dəqiqə, h = saat, d = gün.
 - /unban <istifadəçi adı/id>: istifadəçini unban edir. (mesajına cavab olaraq da yaza bilərsiz)
 - /kick <istifadəçi adı/id>: admin olduğunuz qrupda seçdiyiniz adamı atır (mesajına cavab olaraq da yaza bilərsiz)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
