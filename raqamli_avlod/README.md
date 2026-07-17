# Raqamli Avlod — O'quv markaz platformasi

## 1-BOSQICH: Loyiha asosi (tayyor)

Bu bosqichda quyidagilar yaratildi:
- Django loyiha skeleti
- 4 xil rolli foydalanuvchi tizimi: **Super Admin, Admin, O'qituvchi, Talaba**
- Kurs, Guruh, Guruh a'zoligi modellari
- Har bir rol uchun alohida panelga kirish (login qilgach avtomatik yo'naltiriladi)
- Faoliyat logi tizimi (kim, qachon, nima qildi)

## O'RNATISH (o'zingizning kompyuteringizda, VS Code'da)

1. Ushbu papkani (`raqamli_avlod`) kompyuteringizga oching.
2. Terminalda (VS Code ichida `Ctrl + ~`) shu papka ichida turib:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

3. Ma'lumotlar bazasini yarating:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. O'zingiz uchun Super Admin foydalanuvchi yarating:

```bash
python manage.py createsuperuser
```
Bu yerda username, email va parol so'raladi. Keyin Django admin panelida
(`http://127.0.0.1:8000/admin/`) shu foydalanuvchining **role** maydonini
qo'lda `super_admin` qilib qo'ying (createsuperuser buni avtomatik to'ldirmaydi).

5. Serverni ishga tushiring:

```bash
python manage.py runserver
```

6. Brauzerda oching:
- `http://127.0.0.1:8000/` — kirish sahifasi (rolga qarab panelga yo'naltiradi)
- `http://127.0.0.1:8000/admin/` — Django'ning tayyor boshqaruv paneli (hozircha
  Super Admin shu orqali kurs/guruh/foydalanuvchi qo'sha oladi, keyingi
  bosqichda buning o'rniga chiroyli maxsus interfeys yaratamiz)

## KEYINGI BOSQICHLAR (rejamiz)

- **2-bosqich:** Super Admin panelini to'liq qilish — admin va o'qituvchilarni
  ro'yxatdan o'tkazish, kurs yaratish, o'qituvchini kursga/guruhga biriktirish,
  barcha faoliyat logini chiroyli ko'rsatish
- **3-bosqich:** Admin panelini to'liq qilish — talabalarni ro'yxatga olish
  (login/parol berish), talabani guruhga biriktirish/chiqarish, nazorat
  ishlarini (haftalik/oylik imtihon) joylash
- **4-bosqich:** O'qituvchi panelini to'liq qilish — dars qo'shish (maruza
  matni bilan), 4 qismli uyga vazifa tizimi:
  1. Video dars (oxirigacha ko'rilmasa keyingisi ochilmaydi)
  2. Topshiriq (3 daraja: oson/o'rtacha/qiyin, har biriga kirish kodi, fayl
     yuklash — .txt/.pdf/.docx)
  3. Savol-javob bo'limi
  4. Quiz/test bo'limi

  Ballar taqsimoti: 1-qism 5 ball, 2-qism 60 ball (10+20+30), 3-qism 10 ball,
  4-qism 15 ball, faollik 10 ball, video ko'rish uchun avtomatik 5 ball
- **5-bosqich:** Talaba panelini to'liq qilish — vazifalarni bajarish,
  "Baholarim" bo'limi, "Reyting" bo'limi (guruh bo'yicha umumiy ball),
  kursni yakunlagach sertifikat berish (Admin tasdig'idan keyin)

Har bir bosqichni birma-bir, siz bilan birga ishlab chiqamiz.

## AI BAHOLASH (Gemini) — ishga tushirish

O'quvchi 2-qism (Topshiriq) yoki Nazorat ishiga javob fayl (`.txt/.pdf/.docx`)
yuklaganda, tizim avtomatik ravishda Google Gemini AI orqali javobni tahlil
qilib, **taklif** sifatida ball va qisqa izoh tayyorlaydi. Bu hech qachon
yakuniy ball emas — O'qituvchi/Admin baholash sahifasida AI taklifini
ko'radi va "Qo'llash" tugmasi bilan qabul qiladi yoki o'zi boshqa ball
qo'yadi.

### 1. Bepul Gemini API kalitini olish
1. https://aistudio.google.com saytiga kiring (Google hisobingiz bilan)
2. "Get API key" tugmasini bosing va yangi kalit yarating
   (to'lov kartasi talab qilinmaydi, bepul limiti yetarli)

### 2. Kalitni loyihaga joylashtirish
Loyihaning **asosiy papkasida** (manage.py bilan bir joyda) `gemini_api_key.txt`
nomli yangi fayl yarating va ichiga faqat kalitni yozib saqlang.
(Yoki `GEMINI_API_KEY` muhit o'zgaruvchisini o'rnatishingiz mumkin.)

### 3. Kerakli paketlarni o'rnatish
```bash
pip install -r requirements.txt
```
(Bu `python-docx` va `pypdf` paketlarini ham o'rnatadi — fayldan matn
ajratib olish uchun kerak.)

**Eslatma:** agar `gemini_api_key.txt` topilmasa, tizim shunchaki AI
baholashni o'tkazib yuboradi — sayt buzilmaydi, faqat AI taklifi
ko'rinmaydi va o'qituvchi/admin baholarni oldingidek qo'lda qo'yadi.

## TELEGRAM BOT — ishga tushirish

Bot Talaba va Kuzatuvchi foydalanuvchilari uchun ishlaydi: saytdagi login/parol
bilan botga kirib, baholarni va reytingni ko'rish, hamda Kuzatuvchi uchun
"Tanishib chiqdim" tugmasini bosish mumkin.

### 1. Bot yaratish
Telegram'da **@BotFather** ga yozing:
1. `/newbot` buyrug'ini yuboring
2. Bot uchun nom va username bering (username `bot` bilan tugashi kerak, masalan `RaqamliAvlodBot`)
3. BotFather sizga bir qatordan iborat **token** beradi (masalan `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

### 2. Tokenni loyihaga joylashtirish
Loyihaning **asosiy papkasida** (manage.py bilan bir joyda) `bot_token.txt`
nomli yangi fayl yarating va ichiga faqat tokenni yozib saqlang (boshqa hech
narsa yozmang, bo'sh qator ham shart emas).

### 3. Kerakli paketni o'rnatish
```bash
pip install -r requirements.txt
```
(Bu `pyTelegramBotAPI` paketini ham o'rnatadi.)

### 4. Botni ishga tushirish
```bash
python bot.py
```
Terminalda "Bot ishga tushdi..." degan xabarni ko'rsangiz, bot ishlayapti.
Bu terminalni ochiq qoldiring (yoki alohida terminalda ishga tushiring —
veb-sayt `runserver` bilan bir vaqtda alohida terminalda ishlaydi).

### 5. Botdan foydalanish
1. Telegram'da botingizni toping va `/start` bosing
2. Saytdagi **login**ingizni yuboring
3. Keyin **parol**ingizni yuboring (xavfsizlik uchun bot bu xabarni chatdan o'chiradi)
4. Muvaffaqiyatli kirgach, tugmalar orqali baholaringizni va reytingni ko'rasiz
5. Qayta kirish yoki boshqa hisobga o'tish uchun `/logout` buyrug'ini yuboring

**Eslatma:** Bot faqat **Talaba** va **Kuzatuvchi** hisoblari uchun ishlaydi.
Super Admin, Admin va O'qituvchi hisoblari bilan botga kirib bo'lmaydi —
ular faqat veb-sayt orqali ishlaydi.
