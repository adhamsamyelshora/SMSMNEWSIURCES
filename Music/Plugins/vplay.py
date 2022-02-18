import asyncio
import os

from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo,
)
from youtubesearchpython import VideosSearch

from Music import BOT_NAME, BOT_USERNAME, app
from Music.config import SUPPORT_GROUP, UPDATES_CHANNEL
from Music.MusicUtilities.helpers.filters import command
from Music.MusicUtilities.helpers.logger import LOG_CHAT
from Music.MusicUtilities.tgcallsrun import ASS_ACC
from Music.MusicUtilities.tgcallsrun.queues import QUEUE, add_to_queue, get_queue
from Music.MusicUtilities.tgcallsrun.music import pytgcalls as call_py


def ytsearch(query):
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return 0


async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()



@app.on_message(command("vplay") & filters.group)
async def vplay(c: Client, message: Message):
    replied = message.reply_to_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("الدعم : 🦸", url=f"https://t.me/{SUPPORT_GROUP}"),
                InlineKeyboardButton("السورس : 🦹", url=f"https://t.me/{UPDATES_CHANNEL}"),
            ]
        ]
    )
    if message.sender_chat:
        return await message.reply_text(
            "انتا لست ادمن **ولم يتم اتخاذ تعليماتك**\n\n» الرجاء التواصل مع مالك الجروب لتكون مشرف"
        )
    try:
        aing = await c.get_me()
    except Exception as e:
        return await message.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await message.reply_text(
            f"""
💡 لاستعمال البوت احتاج المزيد من الصاليحات:

» ❌ حذف الرسايل
» ❌ حظر مستخدمين
» ❌ داعوه المستخدمين عبر الرابط
» ❌ بدأ المحادثات الصوتيه 

✨ مدعوم من: [{BOT_NAME}](t.me/{BOT_USERNAME})
""",
            disable_web_page_preview=True,
        )
        return
    if not a.can_manage_voice_chats:
        await message.reply_text(
            f"""
💡 احتاج أن أكون مشرف بصلاحية

» ❌ بدأ المحدثات الصوتيه 

✨ مدعوم من: [{BOT_NAME}](t.me/{BOT_USERNAME})
""",
            disable_web_page_preview=True,
        )
        return
    if not a.can_delete_messages:
        await message.reply_text(
            f"""
💡 احتاج أن أكون مشرف بصلاحية:

» ❌ حذف الرسائل

✨ مدعوم من: [{BOT_NAME}](t.me/{BOT_USERNAME})
""",
            disable_web_page_preview=True,
        )
        return
    if not a.can_invite_users:
        await message.reply_text(
            f"""
💡 احتاج أن أكون مشرف بصلاحية:

» ❌ داعوه المستخدمين عبر الرابط

✨ مدعوم من: [{BOT_NAME}](t.me/{BOT_USERNAME})
""",
            disable_web_page_preview=True,
        )
        return
    try:
        ubot = await ASS_ACC.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await message.reply_text(
                f"@{ubot.username} **Terkena ban di grup** {message.chat.title}\n\n» **unban Assistant terlebih dahulu jika ingin menggunakan bot ini.**"
            )
            return
    except UserNotParticipant:
        if message.chat.username:
            try:
                await ASS_ACC.join_chat(message.chat.username)
            except Exception as e:
                await message.reply_text(
                    f"❌ **@{ubot.username} فشل المساعد في الانضمام**\n\n**السبب**: `{e}`"
                )
                return
        else:
            try:
                invite_link = await message.chat.export_invite_link()
                if "+" in invite_link:
                    link_hash = (invite_link.replace("+", "")).split("t.me/")[1]
                await ASS_ACC.join_chat(f"https://t.me/joinchat/{link_hash}")
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                return await message.reply_text(
                    f"❌ **@{ubot.username} فشل المساعد في الانضمام**\n\n**السسب**: `{e}`"
                )

    if replied:
        if replied.video or replied.document:
            what = "Audio Searched"
            await LOG_CHAT(message, what)
            loser = await replied.reply("🦸 **جاري التحميل...**")
            dl = await replied.download()
            link = replied.link
            if len(message.command) < 2:
                Q = 720
            else:
                pq = message.text.split(None, 1)[1]
                if pq == "720" or "480" or "360":
                    Q = int(pq)
                else:
                    Q = 720
                    await loser.edit(
                        "» **مسموح فقط 720 ، 480 ، 360** \n💡 **الآن يمكنك بث الفيديو بدقة 720 بكسل**"
                    )
            try:
                if replied.video:
                    songname = replied.video.file_name[:70]
                    duration = replied.video.duration
                elif replied.document:
                    songname = replied.document.file_name[:70]
                    duration = replied.document.duration
            except BaseException:
                songname = "Video"

            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                await app.send_message(
                    chat_id,
                    f"""
💡 **تمت إضافة المسارات إلى قائمة الانتظار**

🏷 **الاسم:** [{songname[:999]}]({link})
⏱️ **المدة:** {duration} **detik**
🎧 **مطلوبة من :** {requester}

#️⃣ **في قائمة الانتظار رقم** {pos}
""",
                    disable_web_page_preview=True,
                    reply_markup=keyboard,
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                await call_py.join_group_call(
                    chat_id,
                    AudioVideoPiped(
                        dl,
                        HighQualityAudio(),
                        amaze,
                    ),
                    stream_type=StreamType().pulse_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                await app.send_message(
                    chat_id,
                    f"""
▶️ **بدأ تشغيل الفيديو**

🏷 **الاسم:** [{songname[:999]}]({link})
⏱️ **المده:** {duration} **detik**
🎧 **مطلوبه من:** {requester}

💬 **اسم الجروب:** {message.chat.title}
""",
                    disable_web_page_preview=True,
                    reply_markup=keyboard,
                )

    else:
        if len(message.command) < 2:
            await message.reply(
                "» خطأ في  **اسم الفيديو** الرجاء **كتابة الاسم الصحيح**"
            )
        else:
            what = "Query Given"
            await LOG_CHAT(message, what)
            loser = await message.reply(" **جاري البحث..🦸**")
            query = message.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 480
            amaze = HighQualityVideo()
            if search == 0:
                await loser.edit("❌ **لم يتم العثور على نتائج.**")
            else:
                songname = search[0]
                url = search[1]
                duration = search[2]
                thumb = search[3]
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await loser.edit(f"❌ تم اكتشاف مشكلة yt-dl \ n \ n »` {ytlink} `")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                        await loser.delete()
                        requester = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                        await app.send_message(
                            chat_id,
                            f"""
💡 **تمت إضافة المسارات إلى قائمة الانتظار**

🏷 **الاسم:** [{songname[:999]}]({url})
⏱️ **المده** {duration}
🎧 **مطلوبه من** {requester}

#️⃣ **في قائمة الانتظار رقم** {pos}
""",
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    else:
                        try:
                            await call_py.join_group_call(
                                chat_id,
                                AudioVideoPiped(
                                    ytlink,
                                    HighQualityAudio(),
                                    amaze,
                                ),
                                stream_type=StreamType().pulse_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                            await loser.delete()
                            requester = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                            await app.send_message(
                                chat_id,
                                f"""
▶️ **بدأ تشغيل الفيديو**

🏷 **الاسم:** [{songname[:999]}]({url})
⏱️ **المده** {duration}
🎧 **مطلوب من** {requester}

💬 **اسم الجروب:** {message.chat.title}
""",
                                disable_web_page_preview=True,
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await loser.delete()
                            await message.reply_text(f"Error: `{ep}`")


@app.on_message(command("vplaylist") & filters.group)
async def playlist(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await m.delete()
            await m.reply(
                f"**🎧 تحت التشغيل الان:** \n[{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][3]}`",
                disable_web_page_preview=True,
            )
        else:
            QUE = f"**🎧 تحت التشغيل الان:** \n[{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][3]}` \n\n**⏯ DAFTAR ANTRIAN:**"
            l = len(chat_queue)
            for x in range(1, l):
                hmm = chat_queue[x][0]
                hmmm = chat_queue[x][2]
                hmmmm = chat_queue[x][3]
                QUE = QUE + "\n" + f"**#{x}** - [{hmm}]({hmmm}) | `{hmmmm}`\n"
            await m.reply(QUE, disable_web_page_preview=True)
    else:
        await m.reply("**❌ لا يوجد شئ شغال**")
