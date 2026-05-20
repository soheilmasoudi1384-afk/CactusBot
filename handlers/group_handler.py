from rubpy import BotClient, Client
from rubpy.bot import filters
from rubpy.bot.models import Message, Keypad, KeypadRow, Button, Update, ChatKeypadTypeEnum, ButtonTypeEnum
from core import db
from utils.texts import *
from rubpy.bot.models import (
    ButtonLink,
    JoinChannelData,
    Update,
    Keypad,
    KeypadRow,
    Button,
)
import re
from core.save_msg import MessageStore
import jdatetime
import unicodedata
import time
import random 

active_riddles = {}
active_quiz = {}
# دیکشنری برای نگهداری زمان پیام‌های کاربران
# ساختار: {group_guid: {user_guid: [time1, time2, ...]}}
SPAM_TRACKER = {}

AUTO_REPLIES = {


    # سلام و احوال پرسی
    ("سلام", "سلاام", "صلام", "سلامم", "hi", "hello"): ["سلام سلام صدتا سلام ☺️🌵" , "علیک سلام عزیزم 🌵" , "سلام ب روی ماهت 🌝🌵" , "سلام چشای کاکتوس🥹🌵" , "سلام ماه کاکتوس 🌙🌵" , "سلام قلب کاکتوس ❤️🌵" , "سلام قشنگم خوبی؟ 🥹🌵" ,"سلام عزیزم چطوری؟ 😍", "سلام"],
    ("صبح بخیر", "صبخیر", "صبح همگی بخیر"): ["صبحت کاکتوسی باشه قشنگم 😍🌵" , "صبح توام بخیر قلب کاکتوس 😘🌵" , "صبحت بخیر خوابالو 😉🌵" , "صب توام بخیر عزیزم ☺️🌵" , "صبح توام بخیر چشااااای کاکتوس 😍🌵" , "صبح قشنگت بخیر باشه ☀️ امیدوارم روز عالی داشته باشی 🌻", "صبح بخیر"],
    ("شب بخیر", "شبتون بخیر", "شوبخیر"): ["خوب بخوابی ، شبت کاکتوسی 😉🌵" , "خوب بخوابی عزیزمممم ، کاکتوس فداتشه 💋🌵" , "شب توام بخیر قلب کاکتوس 😊🌵" , "شبت پرستاره عزیزم ✨ خوابای خوب ببینی 😴", "شب بخیر"],
    
    # صدا زدن ربات
    ("ربات" , "robot" , "robat" ): ["میشه کاکتوس صدام کنی؟ 🥹🌵" , "لطفا بگو کاکتوس 😭🌵" , "تا نگی کاکتوس باهات حرف نمیزنم 😂🌵" , "اسم من کاکتوسه 🦦🌵" , "باید کاکتوس صدام کنی تا جوابتو بدم 😕🌵" , "اسمم کاکتوسه خسته شدم انقد گفتین ربات اح 😔🌵", "اگه دوسم داری بگو کاکتوس"],
    ("بات" , "bot"): ["منو میگی؟ من کاکتوسم قشنگم ☺️🌵" , "وا بات چیه ، بگو کاکتوس 😕🌵" , "بگی بات باهات قهر میکنما ، اسمم کاکتوسه 😊🌵" , "بات؟؟😳😳 ، اسم من کاکتوسه"],
    ("کسی نیست"): ["من هستم عزیزم"],
    ("کاکتوس"): ["جوووون دلم بگو 😊🌵" , "جانم عزیزم ☺️🌵" , "اووه، کاکتوس ضعفش گرفت! 😄 صدام کردی جونم 🌵" , "اوف، کاکتوس فدات شه، رفیق 😘🌵" , "اوف قربون اون صدات، چی می‌خوای🌵" , "جان کاکتوس! 🌵" , "جانم! 😄🌵" , "اوف، کاکتوس قربونت بره! 🌵" , "کاکتوس به فدات 🌈" , "جانم عزیزمممم"],
    
    # تشکر و خداحافظی
    ("خداحافظ", "بای", "فعلا", "خدافظ"): ["فعلا قشنگم" , "فعلا عزیزم" , "مراقبت کن" , "مراقب خودت باش، زود برگردیا! 👋", "بای بای"],
    



 # فال
    ("فال گیری", "فال", "فال حافظ", "طالع", "طالع بینی"): [
    "📌 بر سر دو راهی قرار گرفته ای. همه ی کارها را سخت می گیری و ناامیدی. فکر می کنی تا حالا زنده بودنت بیخود بوده و تلاش هایت هدر رفته و خود را گول زده ای ولی این را بدان که از هر جا شروع کنی با منفعت است. با تجربه ای که به دست آورده ای تصمیم بگیر و راهت را انتخاب کن. 💫",
    "📌 ریا و تکبر را از خود دور کن و دوباره با دقت به خود و اعمال خود نگاه کن. جنبه های منفی را رها کن و از ضعف های خود تجربه کسب کن تا به مقصود برسی. وقت خود را بیهوده تلف نکن. 😊",
    "📌 درد دل زیادی داری که نمی توانی به هر کسی بگویی. رو به سوی معشوق خود می کنی ولی او هم صدای دل شما را نمی شنود و رو برمی گرداند و از بی تفاوتی همه دل تنگ هستی. خودت فردی پاکدل هستی به خدایت توکل کن و بدان اگر خدا بخواهد مراد دلت را خواهد داد. 📨",
    "📌 دودلی و تردید را از خود دور کن. از همنشینان و دوستان بد دوری کن تا دچار رنج و گمراهی نشوی. آرزوهای دور و دست نیافتنی غیر از رنج و زحمت نتیجه ای ندارد. اعتدال و میانه روی را پیشه کن ✨",
    "📌 خودتان را با خیال و رویا گول نزنید و به واقعیات فکر کنید. ناامیدی را کنار بگذارید، خداوند توبه و بازگشت تان را می پذیرد و شما را از سردرگمی نجات می دهد. چهار چیز باعث نجاتتان می شود: خداوند، نماز، ایمان، قرآن. با این چهار چیز روزگارتان تغییر می کند و به شکوه و شوکت می رسید. 💛",
    "📌 به زودی به آرزوی خود خواهی رسید. خداوند را سپاسگزار باش. مراقب باش پیروزی، تو را دچار غرور و تکبر ننماید. همچنان با اراده و محکم باش تا پیروزی تو مستدام و پایدار باشد. 🚀",
    "📌 غرور و تکبر را از خود دور کن و شک و دودلی را از خود بران. به سخن ناصحان مشفق گوش کن. اگر چه توجهی به مال دنیا نداری اما کوشش و تلاش را در زندگی خود فراموش نکن. در غیر این صورت دچار مشکل خواهی شد. 🌈",
    "📌 وضع دنیا همیشه به یک روال باقی نمی ماند. بنابراین عاقبت اندیش باش و در کارها شتاب و عجله نکن. با خوش بینی به آینده بنگر. با دشواریهای زندگی شجاعانه مقابله کن و نا امید نباش. 🔆",
    "📌 به زودی به هدف و آرزوی خود خواهی رسید و روزگار سعادت و نیکبختی فرا می رسد. بدخواهی و حسادت دیگران تأثیری در اراده تو نخواهد داشت. اعتماد به نفس خود را بیشتر کن. عشق و محبت را سرلوحه ی کار خود قرار بده. 🌿",
    "📌 گردش روزگار به کام تو است و اگر دچار مختصر رنج و غمی شدی، نگران نباش. خونسرد باش و حوصله کن. با همه ی مردم مدارا کن و مغرور نباش. خداوند را شکرگزار باش و قدر نعمات او را بدان و به دیگران محبت کن. 💬",
    "📌 اگر بدون فکر و اندیشه به کاری که داری ادامه بدهی، نتیجه ای جز شکست نخواهی برد. گمان نکن که راه رسیدن به مقصود دشوار است. هیچ مشکلی وجود ندارد که آسان نشود. عقل و اندیشه را راهنمای خود قرار ده. 💛",
    "📌 در زندگی، تکرو و منزوی نباش. در زندگی اجتماعی به وجود دوستان و همراهان نیاز خواهی داشت. به دیگران کمک کن تا در صورت نیاز به یاری تو بشتابند. از زندگی لذت ببر و خود را گرفتار غم های بیهوده نکن. 📨",
    "📌 همه چیز در زندگی شما به نظر عالی می‌رسد، در حال حاضر هم دارای آرامش ذهنی هستید و هم آرامش مالی، بهتر است این آرامش‌ها را با تصورات خیالی و بد بر هم نزنید. زیرا ممکن است شما این تفکر را داشته باشید که اگر به این مسیر قدم گذاشته اید و موفق نیز شده اید، به راحتی می‌توانید در مسیرهای دیگر نیز قدم گذاشته و موفق شوید. این تفکر را نداشته باشید زیرا ممکن است شما را مغرور کند و از جایگاهی که در حال حاضر هستید به پایین پرتاب شوید. شما فردی هستید که اگر در درون‌تان نیز دارای نگرانی‌های زیادی باشید نیز باز به خودتان مسلط هستید و می‌توانید تصمیم درستی را اتخاذ کنید. ✨",
    "📌 شما فردی هستید که به تازگی تصمیمات‌تان را در دقیقه نود می‌گیرید. اگر قرار باشد در رابطه با موضوعی تصمیم بگیرید، این تصمیم را نمی‌گیرید تا آن که از طرف دیگران بر شما اجباری واقع شود. بهتر است به این کار خود پایان دهید زیرا مواقعی پیش می‌آید که ضررهای بسیاری متحمل شوید و یا این که سود و منفعتی را که باید به دست بیاورید به خاطر تعلل از دست می‌دهید. بخصوص اگر شخصی را دوست دارید و تصمیم دارید با او ازدواج کنید توصیه می‌کنیم که این موضوع را به تعویق نیندازید زیرا ممکن است شخصی که او را دوست دارید ازدواج کند. 🌱",
    "📌 شما در این روزها سر درگم شده اید زیرا بسیاری از کارهایی را که قصد انجام شان را دارید مانده اند و به نوعی شما در بین این همه کار ناتمام گیر افتاده‌اید. متاسفانه باید بگوییم سختی‌هایی که در گذشته متحمل شده اید هنوز به پایان نرسیده اند و دوباره سختی‌های جدیدی بر سر راه شما به وجود خواهند آمد. بهتر است در برابر هیجانات خود ایستادگی کنید تا شما را به راه‌های نادرست منحرف نکنند. 🌿",
    "📌 شما معنای واژها و اتفاقاتی را که در زندگی تان پیش می‌اید را به خوبی می‌دانید اما نمی‌توانید تصمیم درست و به موقعی بگیرید بهتر است در این جنبه روحی تان تجدید نظر کنید. در این روزها یک نفع مالی بزرگی به شما می‌رسد بهتر است برای استفاده بهینه از این سود مالی با دیگران وارد مشورت شوید. 🚪",
    "📌 شما فردی هستید که در معرض دید دیگران هستید، دیگران همیشه شما را با نگاه تحسین مشاهده می‌کنند، به همین علت در تصمیم گیری‌های تان مغرور شده‌اید و فکر می‌کنید که شما از افراد دیگر بالاتر هستید، شاید این موضوع صحت داشته باشد اما هنگامی‌که شخصی از شما کمکی می‌خواهد بهتر است به او کمک کنید. 💬",
    "📌 شما بزرگترین شانس زندگی تان را در روزهای آینده تجربه خواهید کرد، بهتر است با فکر و منطق مطلق پیش بروید، مانع احساسات تان شوید و اجازه ندهید تنها احساسات تان شما را پیش ببرد زیرا در این صورت شانس خود را به راحتی از دست خواهید کرد. ⚡",
    "📌 شما برای انجام کارهایتان بیش از حد از دیگران کمک می‌گیرید، فکر نمی‌کنید که دیگر زمان آن فرا رسیده است که خودتان به تنهایی تصمیم بگیرید البته می‌توانید از تجربه‌های یا مشورت‌های دیگران نیز بهره ببرید اما حرف آخر را خودتان بزنید. 💡",
    "📌 شما احساس می‌کنید نیرو یا شخص مافوق الطبیعی مانع از پیشرفت شما می‌شود. زیرا به هر سمتی می‌روید که با در های بسته روبرو می‌شوید اما این افکار شما در ست نیست، چون اکنون زمان مناسبی برای بازدهی نتیجه تلاش‌های شما نمی‌باشد. بهتر است کماکان به تلاش‌های خود ادامه دهید زیرا پاداشی را که هیچ وقت تصورش را نمی‌کنید، منتظر شما ست. 🌈",
    "📌 شما برای این که باور کنید که وجود خارجی دارید، حتما به تایید یا تمجید اشخاص دیگر احتیاج دارید، شما به اشخاص دیگر بیش از حد وابسته هستید. سعی کنید این احساس مخرب را کنار بگذارید زیرا به شدت دید شما را نسبت به زندگی منفی کرده است. شما به جای این کار می‌توانید از تجربه‌های دیگران استفاده کنید نه اینکه تنها وجودتان، زندگی تان در شخص دیگری خلاصه شده باشد. از زندگی تان لذت ببرید. 🔎",
    "📌 فعالیت‌هایی که در این روزهای اخیر انجام داده اید باعث شده است که تا حدودی گیج و گمراه شوید، بهتر است قبل از ادامه ی مسیر در ابتدا به آینده فعالیت‌هایتان نظری داشته باشید، یا یک برنامه ریزی کوتاه مدت داشته باشید و بعد به پیش بروید تا بیش از این گمراه نشوید. از افرادی که در این زمینه دارای تجربه هستند کمک بگیرید. زیرا اگر بدون مشورت به کارهایتان ادامه بدهید، فعالیت‌هایتان دیگر لذتی برای تان ندارد. 🏃‍♂️💨",
    "📌 خوشبختانه، سربالایی زندگی تان رو به اتمام است، مشکلات تان به پایان رسیده است. اکنون زندگی تان در سراشیبی قرار گرفته است، بدون هیچ گونه سعی و تلاشی به تمام اهداف تان می‌رسید. فقظ بنشینید و از زندگی تان لذت ببرید و البته شاکر خداوند نیز باشید. 💛",
    "📌 شما فکر می‌کنید که مدام سختی‌ها و مشکلات دنیا در هر روز و هر ساعت تنها به سر شما می‌ریزد، بهتر است عاقلانه و منطقی به زندگی تان بنگرید نه این که مدام با احساسات تان تصمیم بگیرید زیرا علت تمام مشکلات تان همین موضوع است که شما احساس را در تمام تصمیم گیری‌های مهم تان جایگزین عقل تان کرده اید، توصیه می‌کنیم تا بیش از این آسیب ندیده اید این کار را ترک کنید. ✨",
    "📌 در این روزها به اطراف و موقعیت‌هایی که برایتان پیش می‌آید با نگاه بی تفاوتی می‌نگرید، به همین دلیل بسیاری از شانس‌ها، یا موقعیت‌هایی که روزها یا حتی سال‌ها منتظر آنها بودید بدون این که شما متوجه باشید از بین رفته اند. از زندگی روزمره تان خیلی فاصله گرفته اید، توصیه می‌کنیم فعالیت‌های روزمرتان را دوباره از سر بگیرید تا به ریتم زندگی سابق تان برگردید. 💆‍♂️",
    "📌 شما شخصی هستید که به پیشرفت‌های و دست آوردهای کوچک خیلی زود قانع می‌شوید، اما این راه درستی نیست، زیرا آینده خوبی را برای خودتان نمی‌توانید بسازید، توصیه می‌کنیم به فکر پیشرفت‌های بزرگتر باشید تا بتوانید راه زندگی تان را با سرعت بیشتری طی کنید البته دارای افکار مثبتی هستید، پس با تلاش بیشتری اقدام کنید. 🍀",
    "📌 شما در سابق برای طی کردن مسیر زندگی تان با برنامه ریزی و طرح بیشتری پیش می‌رفتید، می‌توان گفت تمام اقداماتی که انجام می‌دادید حساب شده بود اما در این روزها تمام کارهایتان را با بی‌برنامگی و عجله انجام می‌دهید. به همین دلیل دچار اضطراب و تشویش بسیاری شده‌اید برای این که به وضعیت سابق تان برگردید توصیه می‌کنیم که به زندگی قبل خود ادامه دهید تا آرامش بیشتری را به دست بیاورید. 💗",
    "📌 امروز مسائل غیر قابل پیش بینی دیوانه تان می‌کنند!! چراکه شما می‌دانید موضوعی شگفت در شرف وقوع است ولی نمی‌دانید که آن چیست! بنابراین آماده شدن برای چنین رویدادی امری غیر ممکن است. بهترین استراتژی برای شما این است که در لحظه حال حضور داشته و آگاه و هوشیار باشید. درحال حاضر برای شما هیچ چیز مهم تر از توجه کردن به آنچه اتفاق می‌افتد نیست. 🔧",
    "📌 ممکن است احساس کنید اگر سرنوشت امروز مقدر می‌شد حتی اگر شما قبلا برنامه‌های دیگری داشتید اکنون می‌خواهید تغییرات عمده ای در زندگی تان ایجاد کنید؛ اما می‌توانید فشاری را که بر روی شماست احساس کنید و بدانید که باید سرانجام از قلب تان پیروی کنید. نیازی نیست که اکنون همه چیز را معکوس کنید. به دنبال ساختار هایی باشید تا زمانیکه راه جدید و مهمی‌یافتید شما را حمایت کنند. 👀",
    "📌 شما باید شکرگذار خدا برای این نعماتی که دارید باشید چیزهایی مثل خانه و خانواده؛ مخصوصا اگر ساختمان استواری برای زندگی تان داشته باشید. اما اکنون ممکن است احساسات پیچیده ای درباره تعهدات شخصی خود داشته باشید که شما را از داشتن آزادی آنطور که می‌خواهید باز می‌دارد. فقط به یاد داشته باشید که روابط خانوادگی مانند یک چاقوی دو لبه هستند و پاداش های آنها بدون مسئولیت داشتن امکان پذیر نیست. سعی کنید امروز مواظب سخن گفتن خود باشید چرا که فردا نتایج آن را خواهید دید. 🚀",
    ],
}


RANDOM_NAMES = [
    # اسم آدم‌ها
    "علی", "رضا", "محمد", "حسین", "مهدی", "امیر", "سعید", "مجید", "فرهاد", "بهروز",
    "فاطمه", "زهرا", "مریم", "سارا", "نرگس", "الهام", "نازنین", "پریسا", "شیدا", "ندا",
    # اسم حیوانات
    "شیر", "ببر", "پلنگ", "گرگ", "روباه", "خرس", "فیل", "زرافه", "کانگورو", "پاندا",
    "عقاب", "شاهین", "کبوتر", "طوطی", "کلاغ", "جغد", "قو", "فلامینگو",
    "دلفین", "نهنگ", "کوسه", "اختاپوس", "ماهی", "صدف",
    # اسم‌های رندوم/خنده‌دار
    "قهرمان", "افسانه", "اسطوره", "جادوگر", "شوالیه", "دزد دریایی", "نینجا", "سامورایی",
    "پادشاه", "ملکه", "شاهزاده", "وزیر", "سردار", "کاپیتان",
    "موز", "سیب", "هندوانه", "انار", "انبه", "توت فرنگی",
    "ستاره", "ماه", "خورشید", "ابر", "رعد", "برق", "باد", "طوفان"
]
# تنظیمات اسپم (قابل تغییر به دلخواه شما)
SPAM_MAX_MESSAGES = 3  # حداکثر پیام مجاز
SPAM_TIME_WINDOW = 3   # در این بازه زمانی (به ثانیه)


LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|@\w+)",
    re.IGNORECASE
)

def load_json_data(filename: str) -> list:
    """بارگذاری داده‌ها از فایل JSON"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "../locales", filename)  
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"خطا در بارگذاری فایل {filename}")
        return []  # بازگشت لیست خالی در صورت خطا

# بارگذاری داده‌ها در هنگام استارت ربات
CHISTAN = load_json_data("chistan.json")
QUIZ_QUESTIONS = load_json_data("quiz.json")
JOKES = load_json_data("joke.json")
TEXT = load_json_data("text.json")

store = MessageStore()

def get_score_rank(score: int) -> str:
    """بازگرداندن نشان و عنوان رتبه بر اساس امتیاز کاربر"""
    if score <= 10:
        return " 🐣 تازه کار"
    elif score <= 50:
        return " 🤔 کنجکاو "
    elif score <= 100:
        return " 🦉 آگاه "
    elif score <= 200:
        return " 🎓 متخصص "
    elif score <= 500:
        return " 👑  فیلسوف "
    else:
        return " 👑🤴👑 نابغه گروه"
def contains_link(text: str) -> bool:
    return bool(LINK_PATTERN.search(text))

pattern = re.compile(r'^تنظیم اخطار\s+(\d+)$')

def parse_warning(text: str):
    match = pattern.match(text)
    if not match:
        return False

    warning_number = int(match.group(1))
    return str(warning_number)


pattern_mute = re.compile(r'^سکوت\s+(\d+)$')

def parse_mute(text: str):
    match = pattern_mute.match(text)
    if not match:
        return False

    mute_number = int(match.group(1))
    return str(mute_number)



pattern_del = re.compile(r'^حذف\s+(\d+)$')

def parse_delete_messages(text: str):
    match = pattern_del.match(text)
    if not match:
        return False

    mute_number = int(match.group(1))
    return str(mute_number)



def parse_add_profanity(text: str):
    pattern = r'^افزودن\s+فحش\s+(\S+)$'
    match = re.match(pattern, text)

    if match:
        return match.group(1)
    else:
        return False
    
def parse_add_forbidden_words(text: str):
    pattern = r'^افزودن\s+غیرمجاز\s+(\S+)$'
    match = re.match(pattern, text)

    if match:
        return match.group(1)
    else:
        return False
    
def parse_delete_profanity(text: str):
    pattern = r'^حذف\s+فحش\s+(\S+)$'
    match = re.match(pattern, text)

    if match:
        return match.group(1)
    else:
        return False
    
def parse_delete_forbidden_words(text: str):
    pattern = r'^حذف\s+غیرمجاز\s+(\S+)$'
    match = re.match(pattern, text)

    if match:
        return match.group(1)
    else:
        return False

def is_crash_code(text: str) -> bool:
    """
    بررسی می‌کند که آیا متن ارسال شده یک کد مخرب/هنگی (Text Bomb) است یا خیر.
    """
    if not text:
        return False

    # ۱. کاراکترهای خطرناک کنترلی و تغییر جهت (Bidi Overrides)
    # این کاراکترها معمولاً برای بهم ریختن رندرینگ متن استفاده می شوند
    dangerous_control_chars = {
        '\u202A', '\u202B', '\u202C', '\u202D', '\u202E', # LRE, RLE, PDF, LRO, RLO
        '\u2066', '\u2067', '\u2068', '\u2069',           # LRI, RLI, FSI, PDI
        '\u0f3c', '\u0f3d'                                # کاراکترهای خاصی که در گذشته باعث کرش iOS میشدند
    }
    
    dangerous_count = sum(1 for char in text if char in dangerous_control_chars)
    # کاربران عادی به ندرت بیش از ۱ یا ۲ بار از این کاراکترها استفاده می‌کنند
    if dangerous_count > 4:
        return True

    # ۲. بررسی کاراکترهای نامرئی (Zero-Width)
    # نکته بسیار مهم: نیم‌فاصله فارسی (\u200C) را نباید جزو این لیست قرار دهیم تا پیام عادی کاربران پاک نشود!
    zero_width_chars = {'\u200B', '\u200D', '\uFEFF'}
    zw_count = sum(1 for char in text if char in zero_width_chars)
    if zw_count > 15:
        return True

    # ۳. بررسی متن‌های Zalgo (ترکیب بیش از حد اعراب و نشانه‌ها روی یک حرف)
    # دسته بندی 'Mn' در یونیکد مربوط به (Mark, Nonspacing) است
    combining_count = 0
    consecutive_combining = 0
    max_consecutive_combining = 0

    for char in text:
        if unicodedata.category(char) == 'Mn':
            combining_count += 1
            consecutive_combining += 1
            if consecutive_combining > max_consecutive_combining:
                max_consecutive_combining = consecutive_combining
        else:
            consecutive_combining = 0

    # اگر روی یک حرف بیش از ۱۵ نشانه/اعراب قرار گرفته باشد (قطعا مخرب است)
    if max_consecutive_combining > 15:
        return True
        
    # اگر طول پیام زیاد باشد و درصد بسیار بالایی از آن فقط اعراب و نشانه‌های چسبان باشد
    if len(text) > 30 and (combining_count / len(text)) > 0.4:
        return True

    # اگر هیچکدام از شرایط بالا برقرار نبود، پیام عادی است
    return False
    
def normalize_answer(ans: str) -> str:
    return ans.strip().replace(" ", "").lower()

def register_group_handlers(bot: BotClient):
    texts = load_texts("locales/texts.json")

    async def check_group(group_guid):
        if await db.get_group_settings(group_guid) == None:
            return False
        else:
            return True
    
    async def check_admin_group(group_guid, user_guid):
        if await db.get_group_member(group_guid, user_guid):
            info = await db.get_group_member(group_guid, user_guid)
            if info["user_rank"] == "owner" or info["user_rank"] == "admin":
                return True
            else:
                return False
            
    async def check_mute(group_guid, user_guid, message_id):
        if await db.is_member_muted(group_guid, user_guid):
            await bot.delete_message(group_guid, message_id)
            return True
        else:
            return False

    
    async def check_user_group(group_guid, user_guid):
        if await db.get_group_member(group_guid, user_guid) == None:
            await db.add_user_to_group(group_guid, user_guid)
            return True
        else:
            return False

    async def check_warning_lock(group_guid, user_guid, reason: str = ""):
        setting = await db.get_group_settings(group_guid)
        if setting["locks"]["warning"] == True:
            await db.increment_member_warning(group_guid, user_guid)
            info = await db.get_group_member(group_guid, user_guid)
            ts = t("lock_warning", texts)
            ts = ts.replace("user_guid", f"〔[مشاهده پروفایل]({user_guid})〕")
            ts = ts.replace("member_war", str(info["warning"]))
            ts = ts.replace("max_war", str(setting["max_warnings"]))
            ts = ts.replace("reason", reason)
            try:
                await bot.send_message(group_guid, ts)
            except:
                pass
            if int(info["warning"]) >= int(setting["max_warnings"]):
                await db.set_member_warning(group_guid, user_guid, 0)
                try:
                    await bot.ban_chat_member(group_guid, user_guid)
                    ts = t("ban_user_by_warning", texts)
                    ts = ts.replace("user_guid", f"〔[مشاهده پروفایل]({user_guid})〕")
                    await bot.send_message(group_guid, ts)
                except:
                    pass
        else:
            ts = t("just_warning_message", texts)
            ts = ts.replace("user_guid", f"〔[مشاهده پروفایل]({user_guid})〕")
            ts = ts.replace("reason", reason)
            
            try:
                await bot.send_message(group_guid, ts)
            except:
                pass
            # در این حالت نیازی به دلیل نیست



    @bot.on_update(filters.group)
    async def group_message_processor(client: BotClient, message: Update):
        group_guid = message.chat_id
        if message.new_message:
            user_guid = message.new_message.sender_id
            message_text = message.new_message.text
            if await check_mute(group_guid, user_guid, message.new_message.message_id):
                return


            await store.save(message.new_message.message_id, group_guid, user_guid)
        elif message.updated_message:
            user_guid = message.updated_message.sender_id
            message_text = message.updated_message.text
            await store.save(message.updated_message.message_id, group_guid, user_guid)
        else:
            return




        # ═══════════════════════════════════════════════════════
        # دستورات ساعت، تاریخ و محاسبه سن
        # ═══════════════════════════════════════════════════════

        # --- ساعت ---
        if message_text in ["ساعت", "تایم", "زمان"]:
            
            now = time.time()
            jdate = jdatetime.datetime.fromtimestamp(now)
            shamsi_time = jdate.strftime("%H:%M:%S")
            day_number = jdate.weekday()
            days_fa = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
            day_name = days_fa[day_number]
            
            await message.reply(t("time", texts).format(time=shamsi_time, day=day_name))
            return

        # --- تاریخ ---
        if message_text == "تاریخ":
            
            jdatetime.set_locale('fa_IR')
            now = time.time()
            jdate = jdatetime.datetime.fromtimestamp(now)
            
            shamsi_date = jdate.strftime("%Y/%m/%d")
            month_name = jdate.strftime("%B")
            day_number = jdate.weekday()
            days_fa = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
            day_name = days_fa[day_number]
            shamsi_time = jdate.strftime("%H:%M:%S")
            
            await message.reply(t("date", texts).format(
                        date=shamsi_date,
                        month=month_name,
                        day=day_name,
                        time=shamsi_time
                    ))
            return

        # --- محاسبه سن ---
        if message_text and message_text.startswith("محاسبه سن"):
            
            DAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
            MONTH_NAMES_FA = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
            JALALI_MONTH_DAYS = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
            
            def fa_to_en(text):
                fa_digits = "۰۱۲۳۴۵۶۷۸۹"
                ar_digits = "٠١٢٣٤٥٦٧٨٩"
                en_digits = "0123456789"
                for i in range(10):
                    text = text.replace(fa_digits[i], en_digits[i])
                    text = text.replace(ar_digits[i], en_digits[i])
                return text
            
            def get_jalali_month_days(year):
                remainder = year % 33
                return 30 if remainder in [1, 5, 9, 13, 17, 22, 26, 30] else 29
            
            def get_days_in_previous_month(year, month):
                if month == 1:
                    return get_jalali_month_days(year - 1)
                return JALALI_MONTH_DAYS[month - 2]
            
            def calculate_age(birth_date, today):
                years = today.year - birth_date.year
                months = today.month - birth_date.month
                days = today.day - birth_date.day
                if days < 0:
                    months -= 1
                    days += get_days_in_previous_month(today.year, today.month)
                if months < 0:
                    years -= 1
                    months += 12
                return years, months, days
            
            def get_day_of_year(month, day, year):
                total = sum(JALALI_MONTH_DAYS[:month - 1]) + day
                if month == 12 and get_jalali_month_days(year) == 30:
                    total += 1
                return total
            
            def days_until_next_birthday(birth_day, birth_month, today):
                this_year_birthday = jdatetime.date(today.year, birth_month, birth_day)
                if this_year_birthday > today:
                    next_birthday = this_year_birthday
                else:
                    next_birthday = jdatetime.date(today.year + 1, birth_month, birth_day)
                diff = next_birthday - today
                return diff.days
            
            def parse_date(date_str):
                date_str = date_str.strip()
                date_str = date_str.replace("-", "/").replace("_", "/").replace(".", "/")
                date_str = re.sub(r"\s+", "", date_str)
                date_str = re.sub(r"/+", "/", date_str)
                
                parts = date_str.split("/")
                if len(parts) != 3:
                    raise ValueError("فرمت تاریخ نامعتبر")
                
                parts = [fa_to_en(p) for p in parts]
                
                try:
                    p0, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2])
                except ValueError:
                    raise ValueError("تاریخ باید شامل اعداد باشد")
                
                if p0 > 31:
                    year, month, day = p0, p1, p2
                else:
                    day, month, year = p0, p1, p2
                
                if not (1300 <= year <= 1500):
                    raise ValueError("سال باید بین 1300 و 1500 باشد")
                if not (1 <= month <= 12):
                    raise ValueError("ماه باید بین 1 تا 12 باشد")
                if not (1 <= day <= 31):
                    raise ValueError("روز باید بین 1 تا 31 باشد")
                
                return year, month, day
            
            birth_text = message_text.replace("محاسبه سن", "").strip()
            
            try:
                birth_year, birth_month, birth_day = parse_date(birth_text)
                
                birth_date = jdatetime.date(birth_year, birth_month, birth_day)
                today = jdatetime.date.today()
                years, months, days = calculate_age(birth_date, today)
                
                birth_weekday = DAYS_FA[birth_date.weekday()]
                birth_month_name = MONTH_NAMES_FA[birth_date.month - 1]
                gdate = birth_date.togregorian()
                day_of_year = get_day_of_year(birth_month, birth_day, birth_year)
                days_left = days_until_next_birthday(birth_day, birth_month, today)
                
                if days_left == 0:
                    birthday_msg = "🎉 **امروز تولدته! تولدت مبارک! 🎂**"
                else:
                    birthday_msg = f"🎈 **{days_left} روز** تا تولد بعدیت مونده"
                
                response = (
                    f"🎂 **┈┅┅━━━━⊰تولد⊱━━━━┅┅┈** 🎂\n\n"
                    f"📅 تاریخ تولد:\n"
                    f"   {birth_year}/{birth_month:02d}/{birth_day:02d}\n\n"
                    f"📆 معادل میلادی:\n"
                    f"   {gdate.year}/{gdate.month:02d}/{gdate.day:02d}\n\n"
                    f"🗓 روز هفته:\n"
                    f"   {birth_weekday}\n\n"
                    f"🌙 ماه تولد:\n"
                    f"   {birth_month_name} (روز {day_of_year} سال)\n\n"
                    f"⏳ سن دقیق:\n"
                    f"   ✦ {years} سال\n"
                    f"   ✦ {months} ماه\n"
                    f"   ✦ {days} روز\n\n"
                    f"{birthday_msg}\n\n"
                    f"**┈┅┅━━━━━⊰CACTUS⊱━━━━━┅┅┈**"
                )
                
                await message.reply(response)
                
            except ValueError as e:
                await message.reply(
                    f"❌ {str(e)}\n\n"
                    "📋 فرمت‌های قابل قبول:\n"
                    "• محاسبه سن 1377/04/11\n"
                    "• محاسبه سن 11/04/1377\n"
                    "• محاسبه سن ۱۳۷۷/۰۴/۱۱\n"
                    "• محاسبه سن ۱۱/۰۴/۱۳۷۷"
                )
            except:
                await message.reply(
                    "❌ فرمت تاریخ اشتباه است\n\n"
                    "📋 فرمت‌های قابل قبول:\n"
                    "• محاسبه سن 1377/04/11\n"
                    "• محاسبه سن 11/04/1377\n"
                    "• محاسبه سن ۱۳۷۷/۰۴/۱۱\n"
                    "• محاسبه سن ۱۱/۰۴/۱۳۷۷"
                )
            return




        is_admin = await check_admin_group(group_guid, user_guid) # فرض بر اینکه این تابع را دارید
        
        if is_admin == False:
            now = time.time()
            
            # ساختاردهی اولیه دیکشنری برای گروه و کاربر
            if group_guid not in SPAM_TRACKER:
                SPAM_TRACKER[group_guid] = {}
            if user_guid not in SPAM_TRACKER[group_guid]:
                SPAM_TRACKER[group_guid][user_guid] = []
                
            # گرفتن لیست زمان پیام‌های قبلی کاربر
            user_timestamps = SPAM_TRACKER[group_guid][user_guid]
            
            # پاک کردن زمان پیام‌های قدیمی که از پنجره زمانی (مثلا ۳ ثانیه) گذشته‌اند
            user_timestamps = [t for t in user_timestamps if now - t <= SPAM_TIME_WINDOW]
            
            # اضافه کردن زمان پیام جدید
            user_timestamps.append(now)
            SPAM_TRACKER[group_guid][user_guid] = user_timestamps
            
            # بررسی اینکه آیا تعداد پیام‌ها در این زمان کوتاه از حد مجاز بیشتر شده؟
            if len(user_timestamps) > SPAM_MAX_MESSAGES:
                # پاک کردن لیست زمان‌ها تا پشت سر هم اخطار ندهد
                SPAM_TRACKER[group_guid][user_guid] = []
                
                # دریافت اطلاعات کاربر و تنظیمات گروه از دیتابیس
                user_info = await db.get_group_member(group_guid, user_guid)
                group_settings = await db.get_group_settings(group_guid)
                
                if user_info and group_settings:
                    max_warnings = group_settings.get("max_warnings", 3)
                    current_warnings = user_info.get("warning", 0)
                    new_warnings = current_warnings + 1
                    
                    if new_warnings >= max_warnings:
                        # --- حالت اول: رسیدن به سقف اخطار -> اخراج کاربر ---
                        try:
                            # در اینجا باید متد اخراج ربات خود را صدا بزنید (بسته به کتابخانه‌ای که استفاده می‌کنید)
                            await bot.ban_chat_member(chat_id=group_guid, user_id=user_guid)
                            # پس از اخراج، کاربر را از دیتابیس پاک کرده یا وضعیتش را بروز کنید
                            group_settings["kicked"] += 1
                            await db.update_group_settings(group_guid, group_settings)
                            
                            await message.reply(t("spam_kick_message", texts).format(
                                user_guid=user_guid, 
                                max_warnings=max_warnings
                            ))
                            try:
                                await bot.delete_message(group_guid, message.new_message.message_id)
                            except:
                                pass
                        except Exception as e:
                            print(f"Error kicking user: {e}")
                    else:
                        # --- حالت دوم: ثبت اخطار جدید ---
                        # بروزرسانی تعداد اخطارهای کاربر در دیتابیس
                        await db.set_member_warning(group_guid, user_guid, new_warnings) # فرض بر اینکه این متد را دارید
                        
                        await message.reply(t("spam_warning_message", texts).format(
                            user_guid=user_guid,
                            new_warnings=new_warnings,
                            max_warnings=max_warnings
                        ))
                    return
        
        if message_text and message_text in ["روشن" , "فعال"]:
            grps = await db.get_all_groups()
            cap = await db.get_group_capacity()
            if await db.get_group_settings(group_guid) == None:
                if len(grps) < cap:
                    group_info = await client.get_chat(group_guid)
                    await db.add_or_update_group(group_guid, group_info.title)
                    await db.add_user_to_group(group_guid, user_guid, "owner")
                    await message.reply(t("start_group", texts))
                else:
                    await message.reply("**🌵 ┅━⊰ مدیریت گروه کاکتوس ⊱━┅ 🌵**\n\n\n⚠️ ظرفیت گروه های این ربات به دلیل حفظ کیفیت ربات تکمیل شده است\n\n✅ لطفاً از دیگر ربات های رایگان کاکتوس استفاده کنید.\n\n🟢 لینک ربات های جایگزین:\n\n@CactussProBot • ربات کاکتوس پرو\n\n@CactussPlusBot • ربات کاکتوس پلاس\n\n**┈┅┅━━━━━⊰CACTUS⊱━━━━━┅┅┈**")
            else:
                await message.reply(t("Pre_enabled", texts))
            return
        
        if await check_group(group_guid):
            group_setting = await db.get_group_settings(group_guid)
            if is_admin == False and group_setting["mute_group"] > 0:
                await bot.delete_message(group_guid, message.new_message.message_id)
                return
            if await check_user_group(group_guid, user_guid):
                if group_setting["welcome"]:
                    await message.reply(group_setting["welcome_message"])
            await db.increment_user_message_count(group_guid, user_guid)
            # User Section
            
            
            
            
            
            if message_text and message_text.strip() in ["آمار", "امار"]:
                target_user_guid = None
                is_other_user = False
                
                # بررسی ریپلای
                if message.new_message.reply_to_message_id:
                    reply_msg_id = message.new_message.reply_to_message_id
                    target_msg_data = await store.get(reply_msg_id)
                    if target_msg_data:
                        target_user_guid = target_msg_data["user_guid"]
                        is_other_user = True
                    else:
                        await message.reply(t("reply_not_found", texts))
                        return
                else:
                    # بدون ریپلای = آمار خود کاربر
                    target_user_guid = user_guid
                
                user_info = await db.get_group_member(group_guid, target_user_guid)
                if user_info:
                    rank_map = {
                        "owner": "👑 مالک گروه",
                        "admin": "👮‍♂️ ادمین",
                        "member": "👤 کاربر عادی"
                    }
                    user_rank_fa = rank_map.get(user_info["user_rank"], "نامشخص")
                    mute_status = "🔇 بله (محدود شده)" if user_info["mute"] > 0 else "🔊 خیر (آزاد)"
                    
                    # دریافت امتیاز سرگرمی کاربر
                    score_info = await db.get_user_score_info(group_guid, target_user_guid)
                    score = score_info["score"] if score_info else 0
                    score_rank = get_score_rank(score)
                    
                    stats_data = {
                        "user_guid": user_info["user_guid"],
                        "rank": user_rank_fa,
                        "total_messages": user_info["message_count"],
                        "today_messages": user_info["messages_today"],
                        "warnings": user_info["warning"],
                        "mute_status": mute_status,
                        "score": score,
                        "score_rank": score_rank
                    }
                    
                    template_key = "target_stats_template" if is_other_user else "user_stats_template"
                    base_text = t(template_key, texts)
                    if "{score}" not in base_text:
                        base_text += "\n🏆 امتیازات سرگرمی: {score}\n🎖 رتبه امتیازی: {score_rank}"
                    await message.reply(base_text.format(**stats_data))
                else:
                    await message.reply(t("user_not_found_stats", texts))
            
            
            
            

                    
                    
                    
                    
                    
                    
                    
                    
                    
            # ==========================================
            # بخش ۱: ثبت و تنظیم اصل
            # دستورات: "ثبت اصل" و "تنظیم اصل"
            # ==========================================
            elif message_text and message_text.startswith(("ثبت اصل", "تنظیم اصل")):
                # تشخیص پیشوند و حذف آن از متن
                if message_text.startswith("ثبت اصل"):
                    mes = message_text.replace("ثبت اصل", "", 1).strip()
                else:
                    mes = message_text.replace("تنظیم اصل", "", 1).strip()
                # بررسی خالی نبودن متن
                if not mes:
                    await message.reply("❌ لطفاً متن اصل را وارد کنید.\n📝 مثال: ثبت اصل من یک برنامه‌نویس هستم")
                    return
                
                # دریافت اطلاعات فعلی کاربر
                current_info = await db.get_user_score_info(group_guid, user_guid)
                
                # ساختار جدید اطلاعات: ترکیب اصل جدید + لقب قبلی
                new_data = {}
                
                if current_info:
                    # اگر رکورد وجود دارد، لقب قبلی را نگه دار
                    existing_nick = current_info.get("user_information", {}).get("nick", "")
                    new_data = {
                        "inf": mes,      # اصل جدید
                        "nick": existing_nick  # لقب قبلی را نگه دار
                    }
                    # به‌روزرسانی رکورد موجود
                    await db.update_user_information(group_guid, user_guid, new_data)
                    await message.reply(t("update_asl", texts))
                else:
                    # اگر رکورد وجود ندارد، رکورد جدید بساز (فقط اصل، لقب خالی)
                    new_data = {
                        "inf": mes,
                        "nick": ""  # لقب هنوز ثبت نشده
                    }
                    await db.set_user_score_info(group_guid, user_guid, new_data)
                    await message.reply(t("set_asl", texts))

            # ==========================================
            # بخش ۲: نمایش اصل خود کاربر
            # دستورات: "اصل من" و "اصلم"
            # ==========================================
            elif message_text and message_text.strip() in ["اصل من", "اصلم"]:
                # چک وجود رکورد per-group
                if await db.get_user_score_info(group_guid, user_guid):
                    info = await db.get_user_score_info(group_guid, user_guid)
                    await message.reply(info["user_information"]["inf"])
                else:
                    await message.reply(t("user_asl_not_found", texts))

            # ==========================================
            # بخش ۳: نمایش اصل کاربر دیگر (با ریپلای)
            # دستورات: "اصل"، "اصل کاربر"، "اصلش"
            # ==========================================
            elif message_text and message_text.strip() in ["اصل", "اصل کاربر"]:
                if message.new_message.reply_to_message_id:
                    reply_msg_id = message.new_message.reply_to_message_id
                    if await store.get(reply_msg_id):
                        target_user = await store.get(reply_msg_id)
                        info_sender = await db.get_group_member(group_guid, target_user["user_guid"])
                        # چک وجود رکورد per-group
                        if await db.get_user_score_info(group_guid, target_user["user_guid"]):
                            info = await db.get_user_score_info(group_guid, target_user["user_guid"])
                            await message.reply(info["user_information"]["inf"])
                        else:
                            await message.reply(t("user_asl_not_found", texts))
                else:
                    # اگر ریپلای نبود، اصل خود کاربر را نشان بده
                    if await db.get_user_score_info(group_guid, user_guid):
                        info = await db.get_user_score_info(group_guid, user_guid)
                        await message.reply(info["user_information"]["inf"])
                    else:
                        await message.reply(t("user_asl_not_found", texts))












               # ==========================================
            # بخش ۱: ثبت و تنظیم اصل
            # دستورات: "ثبت اصل" و "تنظیم اصل"
            # ==========================================
            elif message_text and message_text.startswith(("ثبت اصل", "تنظیم اصل")):
                # تشخیص پیشوند و حذف آن از متن
                if message_text.startswith("ثبت اصل"):
                    mes = message_text.replace("ثبت اصل", "", 1).strip()
                else:
                    mes = message_text.replace("تنظیم اصل", "", 1).strip()
                
                # بررسی خالی نبودن متن
                if not mes:
                    await message.reply("❌ لطفاً متن اصل را وارد کنید.\n📝 مثال: ثبت اصل من یک برنامه‌نویس هستم")
                    return
                
                # دریافت اطلاعات فعلی کاربر
                current_info = await db.get_user_score_info(group_guid, user_guid)
                
                # ساختار جدید اطلاعات
                new_data = {}
                
                if current_info:
                    # اگر رکورد وجود دارد، لقب قبلی را نگه دار
                    existing_nick = ""
                    if current_info.get("user_information"):
                        existing_nick = current_info["user_information"].get("nick", "")
                    
                    new_data = {
                        "inf": mes,
                        "nick": existing_nick
                    }
                    await db.update_user_information(group_guid, user_guid, new_data)
                    await message.reply(t("update_asl", texts))
                else:
                    # اگر رکورد وجود ندارد، رکورد جدید بساز
                    new_data = {
                        "inf": mes,
                        "nick": ""
                    }
                    await db.set_user_score_info(group_guid, user_guid, new_data)
                    await message.reply(t("set_asl", texts))

            # ==========================================
            # بخش ۲: نمایش اصل خود کاربر
            # ==========================================
            elif message_text and message_text.strip() in ["اصل من", "اصلم"]:
                current_info = await db.get_user_score_info(group_guid, user_guid)
                
                if current_info and current_info.get("user_information"):
                    inf = current_info["user_information"].get("inf", "")
                    if inf:
                        await message.reply(inf)
                    else:
                        await message.reply("❌ شما هنوز اصلی ثبت نکرده‌اید.\n📝 برای ثبت: ثبت اصل [متن]")
                else:
                    await message.reply("❌ شما هنوز در سیستم ثبت نشده‌اید.\n📝 برای ثبت: ثبت اصل [متن]")

            # ==========================================
            # بخش ۳: نمایش اصل کاربر دیگر (با ریپلای)
            # ==========================================
            elif message_text and message_text.strip() in ["اصل", "اصل کاربر"]:
                if message.new_message.reply_to_message_id:
                    reply_msg_id = message.new_message.reply_to_message_id
                    target_user = await store.get(reply_msg_id)
                    
                    if target_user:
                        target_info = await db.get_user_score_info(group_guid, target_user["user_guid"])
                        
                        if target_info and target_info.get("user_information"):
                            inf = target_info["user_information"].get("inf", "")
                            if inf:
                                await message.reply(inf)
                            else:
                                await message.reply("❌ این کاربر هنوز اصلی ثبت نکرده است.")
                        else:
                            await message.reply("❌ اطلاعات این کاربر یافت نشد.")
                    else:
                        await message.reply("❌ کاربر مورد نظر یافت نشد. لطفاً دوباره ریپلای کنید.")
                else:
                    # اگر ریپلای نبود، اصل خود کاربر را نشان بده
                    current_info = await db.get_user_score_info(group_guid, user_guid)
                    
                    if current_info and current_info.get("user_information"):
                        inf = current_info["user_information"].get("inf", "")
                        if inf:
                            await message.reply(inf)
                        else:
                            await message.reply("❌ شما هنوز اصلی ثبت نکرده‌اید.\n📝 برای ثبت: ثبت اصل [متن]")
                    else:
                        await message.reply("❌ شما هنوز در سیستم ثبت نشده‌اید.\n📝 برای ثبت: ثبت اصل [متن]")

            # ==========================================
            # بخش ۴: ثبت و تنظیم لقب
            # ==========================================
            elif message_text and message_text.startswith(("ثبت لقب", "تنظیم لقب")):
                if message_text.startswith("ثبت لقب"):
                    mes = message_text.replace("ثبت لقب", "", 1).strip()
                else:
                    mes = message_text.replace("تنظیم لقب", "", 1).strip()
                
                if not mes:
                    await message.reply("❌ لطفاً لقب مورد نظر را وارد کنید.\n📝 مثال: ثبت لقب من یک قهرمان")
                    return
                
                current_info = await db.get_user_score_info(group_guid, user_guid)
                new_data = {}
                
                if current_info:
                    existing_inf = ""
                    if current_info.get("user_information"):
                        existing_inf = current_info["user_information"].get("inf", "")
                    
                    new_data = {
                        "inf": existing_inf,
                        "nick": mes
                    }
                    await db.update_user_information(group_guid, user_guid, new_data)
                    await message.reply("✅ لقب شما با موفقیت ثبت/تغییر شد.")
                else:
                    new_data = {
                        "inf": "",
                        "nick": mes
                    }
                    await db.set_user_score_info(group_guid, user_guid, new_data)
                    await message.reply("✅ لقب شما با موفقیت ثبت شد.")

            # ==========================================
            # بخش ۵: نمایش لقب خود کاربر
            # ==========================================
            elif message_text and message_text.strip() in ["لقب من", "لقبم"]:
                current_info = await db.get_user_score_info(group_guid, user_guid)
                
                if current_info and current_info.get("user_information"):
                    nick = current_info["user_information"].get("nick", "")
                    if nick:
                        await message.reply(f"🏷️ لقب شما: {nick}")
                    else:
                        await message.reply("❌ شما هنوز لقبی ثبت نکرده‌اید.\n📝 برای ثبت: ثبت لقب [لقب]")
                else:
                    await message.reply("❌ شما هنوز در سیستم ثبت نشده‌اید.\n📝 برای ثبت: ثبت لقب [لقب]")

            # ==========================================
            # بخش ۶: نمایش لقب کاربر دیگر (با ریپلای)
            # ==========================================
            elif message_text and message_text.strip() in ["لقب", "لقب کاربر"]:
                if message.new_message.reply_to_message_id:
                    reply_msg_id = message.new_message.reply_to_message_id
                    target_user = await store.get(reply_msg_id)
                    
                    if target_user:
                        target_info = await db.get_user_score_info(group_guid, target_user["user_guid"])
                        
                        if target_info and target_info.get("user_information"):
                            nick = target_info["user_information"].get("nick", "")
                            if nick:
                                await message.reply(f"🏷️ لقب کاربر: {nick}")
                            else:
                                await message.reply("❌ این کاربر هنوز لقبی ثبت نکرده است.")
                        else:
                            await message.reply("❌ اطلاعات این کاربر یافت نشد.")
                    else:
                        await message.reply("❌ کاربر مورد نظر یافت نشد. لطفاً دوباره ریپلای کنید.")
                else:
                    current_info = await db.get_user_score_info(group_guid, user_guid)
                    
                    if current_info and current_info.get("user_information"):
                        nick = current_info["user_information"].get("nick", "")
                        if nick:
                            await message.reply(f"🏷️ لقب شما: {nick}")
                        else:
                            await message.reply("❌ شما هنوز لقبی ثبت نکرده‌اید.\n📝 برای ثبت: ثبت لقب [لقب]")
                    else:
                        await message.reply("❌ شما هنوز در سیستم ثبت نشده‌اید.\n📝 برای ثبت: ثبت لقب [لقب]")




            elif message_text and message_text.strip() == "دیباگ":
                    current_info = await db.get_user_score_info(group_guid, user_guid)
                    
                    if current_info:
                        user_inf = current_info.get("user_information", {})
                        inf = user_inf.get("inf", "ندارد")
                        nick = user_inf.get("nick", "ندارد")
                        
                        await message.reply(
                            f"🔍 اطلاعات شما:\n\n"
                            f"📌 اصل: {inf}\n"
                            f"🏷️ لقب: {nick}\n"
                            f"📊 کل اطلاعات: {current_info}"
                        )
                    else:
                        await message.reply("❌ اطلاعاتی یافت نشد.\n📝 ابتدا یک پیام ارسال کنید تا در دیتابیس ثبت شوید.")
                    
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
            elif message_text and message_text in ["جک", "جوک"]:
                if not group_setting["features"]["entertainment"]:
                    return
                joke = random.choice(JOKES)
                
                await message.reply(joke["joke"])
                            
                            
   
            elif message_text and message_text in ["تکست", "بیو"]:
                if not group_setting["features"]["entertainment"]:
                    return
                text = random.choice(TEXT)
                
                await message.reply(text["text"])
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            

                            
                            
            elif message_text and message_text == "چیستان":
                if not group_setting["features"]["entertainment"]:
                    return
                riddle = random.choice(CHISTAN)

                active_riddles[user_guid] = riddle

                await message.reply(
                    f"چیستان:\n{riddle['question']}\n\n"
                    "وقتی آماده بودی، اینطوری جواب بده:\n"
                    "جواب چیستان <جواب تو>"
                )
            elif message_text and message_text.startswith("جواب چیستان"):
                mes = message_text.replace("جواب چیستان", "").strip()
                if user_guid not in active_riddles:
                    await message.reply("الان چیستان فعالی برای شما ثبت نشده. اول بنویس «چیستان» تا یکی برات بفرستم.")
                    return

                correct_answer = active_riddles[user_guid]["answer"]
                if normalize_answer(mes) == normalize_answer(correct_answer):
                    # افزایش امتیاز
                    if await db.get_user_score_info(group_guid, user_guid):
                        await db.increment_user_score(group_guid, user_guid)
                    else:
                        await db.set_user_score_info(group_guid, user_guid, score=1)
                    
                    # دریافت امتیاز جدید و رتبه
                    score_info = await db.get_user_score_info(group_guid, user_guid)
                    new_score = score_info["score"] if score_info else 0
                    rank_emoji = get_score_rank(new_score)
                    
                    await message.reply(
                        f"آفرین 👏 کارت درسته! 🎉\n\n"
                        f"🏆 امتیازات شما: {new_score}\n"
                        f"🎖 رتبه امتیازی: {rank_emoji}"
                    )
                    del active_riddles[user_guid]
                else:
                    # دریافت امتیازات فعلی (بدون تغییر)
                    score_info = await db.get_user_score_info(group_guid, user_guid)
                    current_score = score_info["score"] if score_info else 0
                    rank_emoji = get_score_rank(current_score)
                    
                    await message.reply(
                        f"نزدیک بود ولی نه 😅\n"
                        f"جواب درست این بود: «{correct_answer}»\n\n"
                        f"🏆 امتیازات شما: {current_score}\n"
                        f"🎖 رتبه امتیازی: {rank_emoji}\n"
                        "بازم می‌تونی بنویسی «چیستان» تا یکی دیگه برات بفرستم."
                    )
                    del active_riddles[user_guid]
            elif message_text and message_text.strip().lower() == "تاس":
                if not group_setting["features"]["entertainment"]:
                    return
                # چند تا الگوی تاس
                dice_patterns = [
                    "🎲", "🎲🎲", "🎲🎲\n  🎲", "🎲🎲\n🎲🎲", "  🎲🎲\n🎲🎲🎲", "🎲🎲🎲\n🎲🎲🎲" 
                ]

                pattern = random.choice(dice_patterns)

                await message.reply(pattern)
            elif message_text and message_text in ["کوییز", "چالش"]:
                if not group_setting["features"]["entertainment"]:
                    return
                if not QUIZ_QUESTIONS:
                    await client.send_text(
                        chat_id=message.chat.group_id,
                        text="فعلاً هیچ سوال چالشی تعریف نشده.",
                    )
                    return

                quiz = random.choice(QUIZ_QUESTIONS)
                active_quiz[user_guid] = quiz

                await message.reply(
                        "چالش برای شما 👇\n\n"
                        f"{quiz['question']}\n\n"
                        "جواب را این‌طوری بفرست:\n"
                        "جواب چالش 1\n"
                        "یا\n"
                        "جواب چالش 2")
            elif message_text and message_text.startswith("جواب چالش"):
                if user_guid not in active_quiz:
                    await message.reply("الان چالشی برای شما ثبت نشده یا این چالش برای شما نیست. اول بنویس «چالش».")
                    return

                try:
                    parts = message_text.split()
                    user_answer_num = int(parts[-1])
                except (ValueError, IndexError):
                    await message.reply("فرمت جواب درست نیست. مثال درست:\nجواب چالش 2")
                    return

                quiz = active_quiz[user_guid]
                correct = quiz["answer"]
                del active_quiz[user_guid]

                if user_answer_num == correct:
                    if await db.get_user_score_info(group_guid, user_guid):
                        await db.increment_user_score(group_guid, user_guid)
                    else:
                        await db.set_user_score_info(group_guid, user_guid, score=1)
                    
                    score_info = await db.get_user_score_info(group_guid, user_guid)
                    new_score = score_info["score"] if score_info else 0
                    rank_emoji = get_score_rank(int(new_score))
                    
                    await message.reply(
                        f"آفرین 👏 کارت عالی بود! 🎉\n\n"
                        f"🏆 امتیازات شما: {new_score}\n"
                        f"🎖 رتبه امتیازی: {rank_emoji}"
                    )
                else:
                    score_info = await db.get_user_score_info(group_guid, user_guid)
                    current_score = score_info["score"] if score_info else 0
                    rank_emoji = get_score_rank(current_score)
                    
                    await message.reply(
                        f"نه، درست نبود 😅\n"
                        f"جواب درست گزینه {correct} بود.\n\n"
                        f"🏆 امتیازات شما: {current_score}\n"
                        f"🎖 رتبه امتیازی: {rank_emoji}"
                    )
                return
            elif message_text and group_setting["features"]["spokesperson_panel"]:
                cleaned_text = message_text.strip().lower()
            
                for triggers, reply_text in AUTO_REPLIES.items():
                    if cleaned_text in triggers:
            
                        # پاسخ‌های معمولی لیست (مثل فال)
                        if isinstance(reply_text, (list, tuple)):
                            selected = random.choice(reply_text)
                        else:
                            selected = reply_text
            
                        await message.reply(str(selected))
                        break
            
            # Locks Section
            if await check_admin_group(group_guid, user_guid) == False and user_guid not in group_setting["lists"]["exempt_users"]:
                locks = group_setting["locks"]
                if locks["text"]:
                    if message_text and message.new_message.file == None:
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال متن")
                if locks["link"]:
                    try:
                        if message_text and contains_link(message_text):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال لینک")
                    except:
                        pass
                    try:
                        if message_text and message.new_message.metadata:
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال لینک")
                    except:
                        pass
                    
                    try:
                        if message.updated_message.text and contains_link(message.updated_message.text):
                            await bot.delete_message(group_guid, message.updated_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ویرایش پیام حاوی لینک")
                        if message.updated_message.text and message.updated_message.metadata:
                            await bot.delete_message(group_guid, message.updated_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ویرایش پیام حاوی لینک")
                    except:
                        pass
                if locks["reply"]:
                    try:
                        if message_text and message.new_message.reply_to_message_id:
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ریپلای کردن")
                    except:
                        pass
                if locks["sticker"]:
                    if message.new_message.sticker != None:
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال استیکر")
                if locks["photo"]:
                    if message.new_message.file != None:
                        f = message.new_message.file.file_name
                        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
                        if f.lower().endswith(image_extensions):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال عکس")    
                if locks["video"]:
                    if message.new_message.file != None:
                        f = message.new_message.file.file_name
                        video_extensions = (
                            '.mp4', '.mkv', '.avi', '.mov', '.wmv',
                            '.flv', '.webm', '.mpeg', '.mpg', '.3gp'
                        )
                        if f.lower().endswith(video_extensions):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال ویدیو")
                if locks["music"]:
                    if message.new_message.file != None:
                        f = message.new_message.file.file_name
                        voice_extensions = (
                            '.ogg', '.opus', '.mp3', '.wav',
                            '.m4a', '.aac', '.flac'
                        )
                        if f.lower().endswith(voice_extensions):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال موزیک")
                if locks["voice"]:
                    if message.new_message.file != None:
                        f = message.new_message.file.file_name
                        voice_extensions = (
                            '.ogg', '.wav'
                        )
                        if f.lower().endswith(voice_extensions):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال ویس")
                if locks["file"]:
                    if message.new_message.file != None:
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال فایل")
                if locks["gif"]:
                    if message.new_message.file != None:
                        f = message.new_message.file.file_name
                        video_extensions = (
                            '.mp4', 'sggsg'
                        )
                        if f.lower().endswith(video_extensions):
                            await bot.delete_message(group_guid, message.new_message.message_id)
                            await check_warning_lock(group_guid, user_guid, "ارسال گیف")
                if locks["profanity"]:
                    pro_list = group_setting["lists"]["profanity"]
                    if message_text and any(c in message_text for c in pro_list):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "استفاده از فحش")
                if locks["forbidden_words"]:
                    for_list = group_setting["lists"]["forbidden_words"]
                    if message_text and any(c in message_text for c in for_list):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "استفاده از کلمه غیرمجاز")
                if locks["english_text"]:
                    if message_text and bool(re.search(r"[A-Za-z]", message_text)):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال متن انگلیسی")
                if locks["edit"]:
                    if message.updated_message and message.updated_message.is_edited:
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ویرایش پیام")
                if locks["emoji"]:
                    EMOJI_PATTERN = re.compile(
                            "["
                            "\U0001F600-\U0001F64F"  # emoticons
                            "\U0001F300-\U0001F5FF"  # symbols & pictographs
                            "\U0001F680-\U0001F6FF"  # transport & map
                            "\U0001F700-\U0001F77F"
                            "\U0001F780-\U0001F7FF"
                            "\U0001F800-\U0001F8FF"
                            "\U0001F900-\U0001F9FF"  # supplemental symbols
                            "\U0001FA00-\U0001FA6F"
                            "\U0001FA70-\U0001FAFF"
                            "]+",
                            flags=re.UNICODE
                        )
                    if message_text and bool(EMOJI_PATTERN.search(message_text)):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال ایموجی")
                if locks["poll"]:
                    if message.new_message and message.new_message.poll:
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ایجاد نظرسنجی")
                if locks["forward"]:
                    if message_text and (message.new_message.forwarded_from or message.new_message.forwarded_no_link):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "فوروارد کردن پیام")  
                if locks["phone_number"]:
                    PHONE_PATTERN = re.compile(
                        r"(\+?\d[\d\-\s]{8,}\d)"
                    )
                    if message_text and bool(PHONE_PATTERN.search(message_text)):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال شماره تلفن")
                if locks["number"]:
                    if message_text and bool(re.search(r"\d", message_text)):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال عدد")
                if locks["hashtag"]:
                    HASHTAG_PATTERN = re.compile(r"#\w+")
                    if message_text and bool(HASHTAG_PATTERN.search(message_text)):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال هشتگ")
                if locks["hang_code"]:
                    if is_crash_code(message_text):
                        await bot.delete_message(group_guid, message.new_message.message_id)
                        await check_warning_lock(group_guid, user_guid, "ارسال کد مخرب (هنگی)")
            # Admins of Group Section
            if await check_admin_group(group_guid, user_guid):
                lock_map = {
                        "متن": "text", "لینک": "link", "آیدی": "id", "استیکر": "sticker",
                        "عکس": "photo", "ویدیو": "video", "ویس": "voice", "فایل": "file",
                        "گیف": "gif", "موزیک": "music", "فحش": "profanity", "کلمات": "forbidden_words",
                        "انگلیسی": "english_text", "ریپلای": "reply", "فوروارد": "forward",
                        "ایموجی": "emoji", "نظرسنجی": "poll", "شماره": "phone_number",
                        "عدد": "number", "هشتگ": "hashtag", "کدهنگی": "hang_code"
                    }
                if message_text and message_text.split()[0] == "قفل":
                    lock = message_text.split()[1]
                    
                    if lock in lock_map:
                        lock_key = lock_map[lock]
                        if group_setting["locks"][lock_key]:
                            await message.reply(t(f"pre_lock_{lock_key}", texts))
                        else:
                            group_setting["locks"][lock_key] = True
                            await db.update_group_settings(group_guid, group_setting)
                            await message.reply(t(f"lock_{lock_key}", texts))
                elif message_text and message_text.split()[0] == "بازکردن":
                    lock = message_text.split()[1]
                    if lock in lock_map:
                        lock_key = lock_map[lock]
                        if not group_setting["locks"][lock_key]:
                            await message.reply(t(f"pre_unlock_{lock_key}", texts))
                        else:
                            group_setting["locks"][lock_key] = False
                            await db.update_group_settings(group_guid, group_setting)
                            await message.reply(t(f"unlock_{lock_key}", texts))
                elif message_text and message_text == "تنظیم اخطار قفل":
                    if group_setting["locks"]["warning"] == False:
                        group_setting["locks"]["warning"] = True
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("set_warning_locks", texts))
                    else:
                        await message.reply(t("pre_set_warning_locks", texts))
                elif message_text and message_text == "حذف اخطار قفل":
                    if group_setting["locks"]["warning"]:
                        group_setting["locks"]["warning"] = False
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("unset_warning_locks", texts))
                    else:
                        await message.reply(t("pre_unset_warning_locks", texts))
                elif message_text and message_text == "اخطار":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            if await check_admin_group(group_guid, target_user["user_guid"]):
                                await message.reply(t("error_warning_to_admin", texts))
                                return
                            await db.increment_member_warning(group_guid, target_user["user_guid"])
                            info = await db.get_group_member(group_guid, target_user["user_guid"])
                            ts = t("warning_message", texts)
                            ts = ts.replace("member_war", str(info["warning"]))
                            ts = ts.replace("max_war", str(group_setting["max_warnings"]))
                            try:
                                await message.reply(ts)
                            except:
                                pass
                            if int(info["warning"]) >= int(group_setting["max_warnings"]):
                                await db.set_member_warning(group_guid, target_user["user_guid"], 0)
                                try:
                                    await bot.ban_chat_member(group_guid, target_user["user_guid"])
                                    await message.reply(t("ban_user_by_warning_2", texts))
                                except:
                                    await message.reply(t("reply_not_found", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text == "حذف اخطار":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            await db.set_member_warning(group_guid, target_user["user_guid"], 0)
                            await message.reply(t("reset_warning", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and parse_warning(message_text):
                    war = int(parse_warning(message_text))
                    if war > 0:
                        group_setting["max_warnings"] = war
                        await db.update_group_settings(group_guid, group_setting)
                        ts = t("set_max_warning", texts)
                        ts = ts.replace("max_war", str(war))
                        await message.reply(ts)
                    else:
                        await message.reply(t("error_set_max_warning", texts))()
                elif message_text and message_text in ["تنظیم ادمین", "تنظیم مدیر"]:
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            info_sender = await db.get_group_member(group_guid, user_guid)
                            if info_user["user_rank"] != "admin" and info_user["user_rank"] != "owner":
                                if info_sender["user_rank"] == "owner":
                                    if await db.set_user_rank(group_guid, target_user["user_guid"], "admin"):
                                        await message.reply(t("add_admin", texts))
                                else:   
                                    await message.reply(t("error_you_not_owner", texts))
                            else:
                                await message.reply(t("error_add_admin", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text in ["تنزیل" , "حذف مدیر" , "حذف ادمین"] :
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            info_sender = await db.get_group_member(group_guid, user_guid)
                            if info_user["user_rank"] == "admin":
                                if info_sender["user_rank"] == "owner":
                                    if await db.set_user_rank(group_guid, target_user["user_guid"], "member"):
                                        await message.reply(t("unset_admin", texts))
                                else:   
                                    await message.reply(t("error_you_not_owner", texts))
                            else:
                                await message.reply(t("error_user_not_admin", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text in ["لیست ادمین", "لیست مدیران", "مدیرها", "ادمین ها", "لیست مدیر"]:
                    admins_list = await db.get_group_admins(group_guid)
                    
                    if not admins_list:
                        await message.reply(t("admin_list_empty", texts))
                    else:
                        text_to_send = t("admin_list_header", texts) + "\n\n"
                        
                        for index, admin in enumerate(admins_list, start=1):
                            admin_guid = admin.get("user_guid", "Unknown")
                            text_to_send += f"{index} - 👤 `[{admin_guid}]`\n"
                            
                        await message.reply(text_to_send)
                elif message_text and parse_mute(message_text):
                    new_count_mute = parse_mute(message_text)
                    if int(new_count_mute) <= 0:
                        await message.reply(t("error_wrong_value", texts))
                        return
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            mute_count = await db.get_member_mute(group_guid, target_user["user_guid"])
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            if info_user["user_rank"] == "member":
                                fin = int(new_count_mute) + int(mute_count)
                                await db.set_member_mute(group_guid, target_user["user_guid"], fin)
                                await message.reply(t("mute_user", texts).replace("value", str(fin)))
                            else:
                                await message.reply(t("error_mute_to_admin", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text.strip() in ["بن", "اخراج"]:
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            if info_user["user_rank"] == "member":
                                try:
                                    await bot.ban_chat_member(group_guid, target_user["user_guid"])
                                    group_setting["kicked"] += 1
                                    await db.update_group_settings(group_guid, group_setting)
                                    await message.reply(t("ban_user", texts))
                                except:
                                    await message.reply(t("error_ban_admin", texts))
                            else:
                                await message.reply(t("error_ban_admin", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and parse_add_profanity(message_text):
                    profanity = parse_add_profanity(message_text)
                    list_of_profanity = group_setting["lists"]["profanity"]
                    list_of_profanity.append(profanity)
                    list_of_profanity = list(set(list_of_profanity))
                    group_setting["lists"]["profanity"] = list_of_profanity
                    await db.update_group_settings(group_guid, group_setting)
                    await message.reply(t("add_profanity", texts))
                elif message_text and parse_add_forbidden_words(message_text):
                    forbidden_words = parse_add_forbidden_words(message_text)
                    list_of_forbidden_words = group_setting["lists"]["forbidden_words"]
                    list_of_forbidden_words.append(forbidden_words)
                    list_of_forbidden_words = list(set(list_of_forbidden_words))
                    group_setting["lists"]["forbidden_words"] = list_of_forbidden_words
                    await db.update_group_settings(group_guid, group_setting)
                    await message.reply(t("add_forbidden_words", texts))
                elif message_text and parse_delete_profanity(message_text):
                    profanity_to_delete = parse_delete_profanity(message_text)
                    list_of_profanity = group_setting["lists"]["profanity"]

                    # چک میکنیم که کلمه در لیست باشد تا ارور ندهد
                    if profanity_to_delete in list_of_profanity:
                        list_of_profanity.remove(profanity_to_delete)
                        group_setting["lists"]["profanity"] = list_of_profanity
                        await db.update_group_settings(group_guid, group_setting)
                        
                        # ارسال پیام موفقیت آمیز
                        response_data = {"word": profanity_to_delete}
                        await message.reply(t("delete_profanity_success", texts).format(**response_data))
                    else:
                        # ارسال پیام در صورتی که کلمه در لیست نباشد
                        response_data = {"word": profanity_to_delete}
                        await message.reply(t("word_not_in_profanity_list", texts).format(**response_data))
                elif message_text and parse_delete_forbidden_words(message_text):
                    forbidden_word_to_delete = parse_delete_forbidden_words(message_text)
                    list_of_forbidden_words = group_setting["lists"]["forbidden_words"]

                    # چک میکنیم که کلمه در لیست باشد تا ارور ندهد
                    if forbidden_word_to_delete in list_of_forbidden_words:
                        list_of_forbidden_words.remove(forbidden_word_to_delete)
                        group_setting["lists"]["forbidden_words"] = list_of_forbidden_words
                        await db.update_group_settings(group_guid, group_setting)
                        
                        # ارسال پیام موفقیت آمیز
                        response_data = {"word": forbidden_word_to_delete}
                        await message.reply(t("delete_forbidden_word_success", texts).format(**response_data))
                    else:
                        # ارسال پیام در صورتی که کلمه در لیست نباشد
                        response_data = {"word": forbidden_word_to_delete}
                        await message.reply(t("word_not_in_forbidden_list", texts).format(**response_data))
                elif message_text and message_text == "معاف":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_sender = await db.get_group_member(group_guid, target_user["user_guid"])
                            if info_sender["user_rank"] == "member":
                                if target_user["user_guid"] not in group_setting["lists"]["exempt_users"]:
                                    list_exempt = group_setting["lists"]["exempt_users"]
                                    list_exempt.append(target_user["user_guid"])
                                    group_setting["lists"]["exempt_users"] = list_exempt
                                    await db.update_group_settings(group_guid, group_setting)
                                    await message.reply(t("add_exempt", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text == "حذف معاف":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_sender = await db.get_group_member(group_guid, target_user["user_guid"])
                            if info_sender["user_rank"] == "member":
                                if target_user["user_guid"] in group_setting["lists"]["exempt_users"]:
                                    list_exempt = group_setting["lists"]["exempt_users"]
                                    list_exempt.remove(target_user["user_guid"])
                                    group_setting["lists"]["exempt_users"] = list_exempt
                                    await db.update_group_settings(group_guid, group_setting)
                                    await message.reply(t("remove_exempt", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and (message_text == "آمار گروه" or message_text == "امار گروه"):
                    today = jdatetime.date.today()
                    date_str = today.strftime("%Y/%m/%d")

                    message_today = await db.get_group_total_messages_today(group_guid)
                    total_message = await db.get_group_total_messages(group_guid)
                    top3 = await db.get_top3_active_members(group_guid)
                    mute = await db.get_muted_members_count(group_guid)

                    kicked = group_setting["kicked"]

                    my_text = t("group_stats_text", texts)
                    values = {
                        "date": date_str,
                        "messages_today": message_today,
                        "total_messages": total_message,

                        "top1_user": f"[کاربر]({top3[0]["user_guid"]})",
                        "top1_count": top3[0]["messages_today"],

                        "top2_user": f"[کاربر]({top3[1]["user_guid"]})",
                        "top2_count": top3[1]["messages_today"],

                        "top3_user": f"[کاربر]({top3[2]["user_guid"]})",
                        "top3_count": top3[2]["messages_today"],

                        "kicked": kicked,
                        "muted": mute
                    }

                    for key, value in values.items():
                        my_text = my_text.replace(key, str(value))
                    await message.reply(my_text)
                elif message_text and parse_delete_messages(message_text):
                    count_del = parse_delete_messages(message_text)
                    list_of_msg_id = await store.get_last_messages(group_guid, int(count_del))
                    if int(count_del) <= 500:
                        x = await message.reply("**♻ در حال پاکسازی منتظر بمانید...**")
                        for msg_id in list_of_msg_id:
                            try:
                                await bot.delete_message(group_guid, msg_id)
                                await store.delete(msg_id)
                            except:
                                pass
                        try:
                            await x.delete()
                        except:
                            pass
                        await bot.send_message(group_guid, t("del_messages", texts).replace("count", count_del))
                    else:
                        await message.reply(t("error_more_500", texts))
                elif message_text and message_text == "لیست قفل":
                    formatted_locks = {}

                    for key, value in group_setting["locks"].items():
                        # اگر قفل True بود یعنی محدودیت فعال است، در غیر این صورت غیرفعال
                        if key != "warning":
                            if value == True:
                                formatted_locks[key] = "✅ فعال"
                            else:
                                formatted_locks[key] = "✖️ غیرفعال"
                    today = jdatetime.date.today()
                    formatted_locks["date"] = today.strftime("%Y/%m/%d")
                    ts = t("rules_text_template", texts)
                    ts = ts.format(**formatted_locks)
                    await message.reply(ts)
                elif message_text and message_text == "لیست فحش":
                    if len(group_setting["lists"]["profanity"]) > 0:
                        pro_list = str(group_setting["lists"]["profanity"])
                        pro_list = pro_list.replace("[", "")
                        pro_list = pro_list.replace("]", "")
                        lists = {
                            "list_of_profanity" : pro_list
                        }
                        txt = t("profanity_list", texts).format(**lists)
                        await message.reply(txt)
                    else:
                        await message.reply(t("profanity_list_is_empty", texts))
                elif message_text and message_text == "لیست غیرمجاز":
                    if len(group_setting["lists"]["forbidden_words"]) > 0:
                        forb_list = str(group_setting["lists"]["forbidden_words"])
                        forb_list = forb_list.replace("[", "")
                        forb_list = forb_list.replace("]", "")
                        lists = {
                            "list_of_forbidden_words" : forb_list
                        }
                        txt = t("forbidden_words_list", texts).format(**lists)
                        await message.reply(txt)
                    else:
                        await message.reply(t("forbidden_words_list_is_empty", texts))
                elif message_text and message_text == "پاکسازی لیست فحش":
                    group_setting["lists"]["profanity"] = []
                    
                    # ذخیره در دیتابیس
                    await db.update_group_settings(group_guid, group_setting)
                    
                    # ارسال پیام موفقیت آمیز
                    await message.reply(t("clear_profanity_success", texts))
                elif message_text and message_text == "پاکسازی لیست غیرمجاز":
                    # قرار دادن یک لیست خالی به جای لیست قبلی
                    group_setting["lists"]["forbidden_words"] = []
                    
                    # ذخیره در دیتابیس
                    await db.update_group_settings(group_guid, group_setting)
                    
                    # ارسال پیام موفقیت آمیز
                    await message.reply(t("clear_forbidden_words_success", texts))
                elif message_text and message_text.startswith(("حاضرجوابی", "حاضر جوابی", "حاظر جوابی", "حاظرجوابی")):
                    mes = message_text.replace("حاضرجوابی", "").replace("حاضر جوابی", "").replace("حاظر جوابی", "").replace("حاظرجوابی", "").strip()
                    if mes == "خاموش":
                        group_setting["features"]["spokesperson_panel"] = False
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("spoken_off", texts))
                    elif mes == "روشن":
                        group_setting["features"]["spokesperson_panel"] = True
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("spoken_on", texts))
                elif message_text and message_text == "حذف سکوت":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            if info_user["user_rank"] == "member":
                                fin = 0
                                await db.set_member_mute(group_guid, target_user["user_guid"], fin)
                                await message.reply(t("unmute_user", texts))
                            else:
                                await message.reply(t("error_mute_to_admin", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                        
                                            
                elif message_text and message_text.startswith(("تنظیم خوشامدگویی", "تنظیم خوش امدگویی", "تنظیم خوشآمدگویی", "تنظیم خوش آمدگویی", "تنظیم خوشامد گویی", "تنظیم خوش امد گویی", "تنظیم خوشآمد گویی", "تنظیم خوش آمد گویی")):
                                        # استخراج متن جدید با حذف کلمه دستور
                    new_welcome = message_text.replace("تنظیم خوشامدگویی", "").replace("تنظیم خوش امدگویی", "").replace("تنظیم خوشآمدگویی", "").replace("تنظیم خوش آمدگویی", "").replace("تنظیم خوشامد گویی", "").replace("تنظیم خوش امد گویی", "").replace("تنظیم خوشآمد گویی", "").replace("تنظیم خوش آمد گویی", "").strip()
                                        
                    
                    if not new_welcome:
                        # اگر فقط دستور را فرستاد و متنی ننوشت
                        await message.reply(t("welcome_text_empty", texts))
                    
                    elif new_welcome == "خاموش":
                        group_setting["welcome"] = False
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("welcome_text_off", texts))
                        return
                    elif new_welcome == "روشن":
                        group_setting["welcome"] = True
                        await db.update_group_settings(group_guid, group_setting)
                        await message.reply(t("welcome_text_on", texts))
                        return
                    else:

                        group_setting["welcome_message"] = new_welcome
                        
                        # ذخیره تنظیمات بروزرسانی شده در دیتابیس
                        await db.update_group_settings(group_guid, group_setting)
                        
                        # ارسال پیام موفقیت به همراه پیش‌نمایش
                        preview_text = new_welcome.replace("{name}", "کاربر تستی").replace("{user_guid}", "123456")
                        success_msg = t("welcome_text_updated", texts) + f"\n\n**پیش‌نمایش:**\n{preview_text}"
                        await message.reply(success_msg)
                                # در همون group_message_processor، بعد از سایر elif ها:
                elif message_text and message_text.startswith("سکوت گروه"):
                    try:
                        parts = message_text.split()
                        if len(parts) >= 3 and parts[2].isdigit():
                            minutes = int(parts[2])
                            group_setting["mute_group"] = minutes
                            await db.update_group_settings(group_guid, group_setting)
                            
                            ts = "✅ گروه برای **{}** دقیقه ساکت شد! 🔇"
                            await message.reply(ts.format(minutes))
                        else:
                            await message.reply("❌ فرمت: `سکوت گروه [عدد]`")
                    except Exception as e:
                        print(e)
                        await message.reply("❌ عدد معتبر وارد کن!")
                elif message_text and message_text == "حذف سکوت گروه":
                    
                    group_setting["mute_group"] = 0
                    await db.update_group_settings(group_guid, group_setting)
                    await message.reply("✅ سکوت گروه **حذف** شد! 🎉")

                elif message_text and message_text == "راهنما":
                    await message.reply(t("list_command", texts))

                elif message_text and message_text in  ["راهنمای تنظیمات" , "راهنمای تنظیمات اصلی"] :
                    await message.reply(t("tanzimat_asli", texts))
                
                elif message_text and message_text in  ["راهنمای مدیریت ادمین" , "راهنمای مدیریت ادمین ها"] :
                    await message.reply(t("admin_modiriyat", texts))
                
                elif message_text and message_text in  ["راهنمای مدیریت کلمات" , "راهنمای مدیریت کلمه"] :
                    await message.reply(t("kalame_modiriyat", texts))
                
                elif message_text and message_text in  ["راهنمای کنترل عضوها" , "راهنمای کنترل اعضا"] :
                    await message.reply(t("kontrol_aza", texts))
                
                elif message_text and message_text in  ["راهنمای قفل ها" , "راهنمای قفل"] :
                    await message.reply(t("gofl_help", texts))
                
                elif message_text and message_text in  ["راهنمای سرگرمی" , "راهنمای سرگرمی ها" , "لیست سرگرمی"] :
                    await message.reply(t("sargarmi_help", texts))
                
                elif message_text and message_text in  ["راهنمای امار" , "راهنمای آمار"] :
                    await message.reply(t("amar_help", texts))

                elif message_text and message_text == "سنجاق":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            await bot.pin_chat_message(group_guid, reply_msg_id)
                            await message.reply(t("pin_message", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text in ["امار امتیازات" , "آمار امتیازات" , "آمار چالش" , "امار چالش"]:
                    top3_scores = await db.get_top3_by_score(group_guid)

                    def safe_get(lst, idx, default=None):
                        try:
                            return lst[idx]
                        except IndexError:
                            return default or {}

                    top1 = safe_get(top3_scores, 0, {"user_guid": None, "score": 0})
                    top2 = safe_get(top3_scores, 1, {"user_guid": None, "score": 0})
                    top3 = safe_get(top3_scores, 2, {"user_guid": None, "score": 0})

                    def make_user_link(user_guid):
                        if not user_guid or user_guid == "-":
                            return "کاربر"
                        return f"[کاربر]({user_guid})"

                    stats_data = {
                        "top1_user": make_user_link(top1.get("user_guid")),
                        "top1_score": top1.get("score", 0) or 0,
                        "top1_rank": get_score_rank(top1.get("score", 0) or 0),
                        "top2_user": make_user_link(top2.get("user_guid")),
                        "top2_score": top2.get("score", 0) or 0,
                        "top2_rank": get_score_rank(top2.get("score", 0) or 0),
                        "top3_user": make_user_link(top3.get("user_guid")),
                        "top3_score": top3.get("score", 0) or 0,
                        "top3_rank": get_score_rank(top3.get("score", 0) or 0),
                    }

                    text_template = t("top_scorers_text", texts)
                    await message.reply(text_template.format(**stats_data), parse_mode="Markdown")
                    return
                elif message_text and message_text.startswith("سرگرمی"):
                    status = message_text.replace("سرگرمی", "").strip()
                    if status == "خاموش":
                        group_setting["features"]["entertainment"] = False
                        await message.reply(t("change_entertainment_off", texts))
                        await db.update_group_settings(group_guid, group_setting)
                    else:
                        group_setting["features"]["entertainment"] = True
                        await message.reply(t("change_entertainment_on", texts))
                        await db.update_group_settings(group_guid, group_setting)
                elif message_text and message_text == "انتقال مالکیت":
                    if message.new_message.reply_to_message_id:
                        reply_msg_id = message.new_message.reply_to_message_id
                        if await store.get(reply_msg_id):
                            target_user = await store.get(reply_msg_id)
                            if user_guid == target_user["user_guid"]:
                                return
                            info_user = await db.get_group_member(group_guid, target_user["user_guid"])
                            info_sender = await db.get_group_member(group_guid, user_guid)
                            if info_sender["user_rank"] == "owner":
                                await db.set_user_rank(group_guid, target_user["user_guid"], "owner")
                                await db.set_user_rank(group_guid, user_guid, "admin")
                                await message.reply(t("change_owner", texts))
                            else:   
                                await message.reply(t("error_you_not_owner", texts))
                        else:
                            await message.reply(t("reply_not_found", texts))
                    else:
                        await message.reply(t("reply_not_found", texts))
                elif message_text and message_text.startswith("تگ "):
                    try:
                        # استخراج عدد
                        count_str = message_text.replace("تگ", "").strip()
                        count = int(count_str)
                        
                        if count < 1:
                            await bot.send_message(group_guid, "❌ تعداد باید بیشتر از 0 باشه!")
                            return
                        
                        if count > 1000:
                            await bot.send_message(group_guid, "❌ حداکثر می‌تونی 50 نفر رو تگ کنی!")
                            return
                        
                        # دریافت اعضای گروه
                        members = await db.get_group_members(group_guid)
                        
                        if not members:
                            await bot.send_message(group_guid, "❌ هیچ عضوی در دیتابیس یافت نشد!")
                            return
                        
                        # انتخاب رندوم
                        selected = random.sample(members, min(count, len(members)))
                        
                        # ساخت پیام تگ
                        tags = []
                        for member in selected:
                            random_name = random.choice(RANDOM_NAMES)
                            tags.append(f"[{random_name}]({member['user_guid']})")
                        
                        message_text = "🔔 " + " | ".join(tags)
                        
                        await bot.send_message(group_guid, message_text)
                        
                    except ValueError:
                        await bot.send_message(group_guid, "❌ فرمت صحیح: تگ <عدد>\nمثال: تگ 10")
                    except Exception as e:
                        print(f"Error in tag command: {e}")
                        await bot.send_message(group_guid, "❌ خطا در تگ کردن!")
                    
                    return