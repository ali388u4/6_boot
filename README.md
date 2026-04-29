# Telegram Bot (aiogram v3) + FastAPI + Postgres + Redis (Clean-ish)

## المتطلبات

- Python 3.12 (لو تشغيل محلي)
- Docker + Docker Compose

## التشغيل عبر Docker

1) انسخ ملف البيئة:

- انسخ `.env.example` إلى `.env`
- عبّئ القيم التالية على الأقل:

- `BOT_TOKEN`
- `WEBHOOK_BASE_URL` (لازم HTTPS عام)
- `OPENAI_API_KEY` (اختياري: فقط لميزة حل سؤال)
- `ADMIN_API_KEY` (مطلوب لتفعيل Admin API)

2) شغّل الخدمات:

- `docker compose up --build`

3) شغّل migrations:

- `docker compose exec api alembic upgrade head`

## Admin API

- كل endpoints تحت `/admin/*`
- يتطلب Header:

- `X-API-Key: <ADMIN_API_KEY>`

### أمثلة (curl)

> ملاحظة: نفّذ على نفس الجهاز الذي يشغّل الخدمة.

#### إنشاء مادة

- `POST /admin/subjects`

```bash
curl -X POST http://localhost:8000/admin/subjects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"name":"رياضيات"}'
```

#### إنشاء فصل

- `POST /admin/chapters`

```bash
curl -X POST http://localhost:8000/admin/chapters \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"subject_id":"<SUBJECT_ID>","title":"الفصل الأول","order_index":1}'
```

#### إنشاء موضوع

- `POST /admin/topics`

```bash
curl -X POST http://localhost:8000/admin/topics \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"chapter_id":"<CHAPTER_ID>","title":"المعادلات","order_index":1}'
```

#### إضافة سؤال (الحل JSON)

- `POST /admin/questions`

```bash
curl -X POST http://localhost:8000/admin/questions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{
    "topic_id":"<TOPIC_ID>",
    "prompt_text":"حل المعادلة: 2x+3=7",
    "solution_json":{
      "steps":[
        {"title":"نطرح 3","explanation":"2x = 4","result":"2x=4"},
        {"title":"نقسم على 2","explanation":"x = 2","result":"x=2"}
      ],
      "final_answer":"x=2"
    },
    "difficulty":1
  }'
```

#### تعريف أسلوب الحل للمادة (يستخدمه OpenAI)

- `PUT /admin/solving-styles`

```bash
curl -X PUT http://localhost:8000/admin/solving-styles \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{
    "subject_id":"<SUBJECT_ID>",
    "style_json":{
      "system_prompt":"You are a math tutor. Return JSON only with steps and final_answer. Use Arabic language." 
    }
  }'
```

## Telegram Webhook

- مسار الـ webhook: `WEBHOOK_PATH` (افتراضي `/telegram/webhook`)
- يتسجل تلقائيًا عند startup بواسطة `BOT_TOKEN` و `WEBHOOK_BASE_URL`

## ملاحظات

- Rate limiting مبني على Redis (`RATE_LIMIT_PER_MINUTE`).
- FSM storage على Redis.
- `UserSessions` يتم تحديثها تلقائيًا (telegram_user_id + fsm_state + state_data + selections).
