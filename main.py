import base64
import os
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Healing the Plant")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_INSTRUCTION = (
    "Ты — эксперт по защите растений. Анализируй фото кратко, по делу и емко. "
    "Отвечай строго по следующей структуре без лишних звездочек Маркдауна:\n\n"
    "🔍 Признаки: (2-3 предложения о том, что видно на фото)\n"
    "🩺 Диагноз: (Точное название болезни, вредителя или проблемы)\n"
    "💊 Способы лечения: (3-4 коротких конкретных шага по исправлению)\n"
    "🛡️ Профилактика: (2-3 ключевых совета на будущее)"
)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Healing the Plant — AI Диагностика растений</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Manrope:wght@200..800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f5f7f2;
            --card: #fff;
            --ink: #173025;
            --muted: #66766e;
            --green: #1f6847;
            --green2: #2e8b60;
            --line: #e0e7e1;
            --soft: #edf5ef;
            --danger: #bd5a45;
        }
        * { box-sizing: border-box; }
        body { margin: 0; background: var(--bg); color: var(--ink); font-family: "DM Sans", sans-serif; }
        
        .topbar {
            height: 72px;
            padding: 0 max(24px, calc((100vw - 1120px)/2));
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #fff;
            border-bottom: 1px solid var(--line);
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .brand { display: flex; gap: 10px; align-items: center; text-decoration: none; color: var(--ink); font-weight: 800; font-size: 21px; }
        .logo { font-size: 25px; }
        .lang-switch { display: flex; background: var(--bg); padding: 4px; border-radius: 12px; }
        .lang-switch button { border: 0; background: transparent; padding: 7px 12px; border-radius: 9px; color: var(--muted); font-weight: 700; cursor: pointer; transition: 0.2s; }
        .lang-switch button.active { background: #fff; color: var(--green); box-shadow: 0 2px 8px #0000000c; }
        
        main { max-width: 1120px; margin: auto; padding: 44px 24px 80px; }
        .hero { min-height: 360px; background: #173b2a; border-radius: 28px; color: #fff; padding: 52px; display: grid; grid-template-columns: 1.3fr .7fr; overflow: hidden; position: relative; }
        .eyebrow { font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--green2); margin: 0 0 10px; }
        .hero .eyebrow { color: #b4e4c9; }
        h1, h2, h3 { font-family: Manrope, sans-serif; margin: 0; }
        h1 { font-size: clamp(38px, 5vw, 62px); line-height: 1.02; max-width: 650px; }
        .heroText { font-size: 17px; line-height: 1.65; color: #d3e2d8; max-width: 650px; margin: 22px 0; }
        .heroBadges { display: flex; gap: 8px; flex-wrap: wrap; }
        .heroBadges span { padding: 8px 12px; background: #ffffff14; border: 1px solid #ffffff20; border-radius: 99px; font-size: 13px; }
        
        /* Иллюстрация растения */
        .plant-art { position: relative; min-height: 270px; }
        .sun { width: 180px; height: 180px; border-radius: 50%; background: #b4e4c9; opacity: .22; position: absolute; right: 15px; top: 0; }
        .stem { position: absolute; width: 10px; height: 190px; background: #9cd4b2; bottom: 10px; right: 125px; border-radius: 10px; transform: rotate(4deg); }
        .leaf { position: absolute; width: 110px; height: 58px; background: #66b58a; border-radius: 100% 0 100% 0; }
        .leaf1 { right: 105px; top: 90px; transform: rotate(-24deg); }
        .leaf2 { right: 170px; top: 145px; transform: scaleX(-1) rotate(-24deg); }
        .pot { position: absolute; right: 70px; bottom: 0; width: 130px; height: 80px; background: #c9825c; clip-path: polygon(10% 0, 90% 0, 76% 100%, 24% 100%); border-radius: 5px; }
        
        /* Карточки и Интерактив */
        .card { background: var(--card); border: 1px solid var(--line); border-radius: 24px; padding: 30px; margin-top: 24px; box-shadow: 0 8px 30px #17302508; }
        .section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 15px; }
        .section-head h2 { font-size: 30px; }
        .status, .ai-chip { font-size: 12px; font-weight: 800; padding: 8px 11px; border-radius: 99px; background: var(--soft); color: var(--green); white-space: nowrap; }
        
        .actions { display: flex; gap: 12px; margin: 25px 0 18px; flex-wrap: wrap; }
        .primary, .secondary, .ghost, .analyze { border: 0; border-radius: 13px; padding: 14px 18px; font: 600 15px "DM Sans"; cursor: pointer; transition: 0.2s; }
        .primary { background: var(--green); color: #fff; }
        .primary:hover { background: var(--green2); }
        .secondary { background: var(--soft); color: var(--green); display: inline-flex; align-items: center; }
        .secondary:hover { background: #e0eee4; }
        .ghost { background: #fff; border: 1px solid #ffffff55; color: #fff; }
        .analyze { width: 100%; background: var(--ink); color: #fff; margin-top: 18px; font-size: 16px; }
        .analyze:hover { background: #234637; }
        .analyze:disabled { opacity: .38; cursor: not-allowed; }
        .privacy { font-size: 12px; color: var(--muted); text-align: center; margin: 12px 0 0; }
        
        .preview { position: relative; max-width: 500px; margin: 18px auto 0; border-radius: 18px; overflow: hidden; background: #eaf0eb; }
        .preview img { width: 100%; max-height: 430px; display: block; object-fit: contain; }
        .remove { position: absolute; right: 10px; top: 10px; width: 35px; height: 35px; border: 0; border-radius: 50%; background: #173025dd; color: #fff; font-size: 20px; cursor: pointer; display: grid; place-items: center; }
        
        .result-text { margin-top: 25px; padding: 22px; background: var(--soft); border-radius: 18px; line-height: 1.7; font-size: 15px; white-space: pre-line; border-left: 5px solid var(--green); }
        .loading { text-align: center; margin-top: 20px; font-weight: 700; color: var(--green); display: none; }
        
        .history-item { background: var(--bg); border: 1px solid var(--line); border-radius: 16px; padding: 18px; margin-top: 12px; }
        .history-date { font-size: 12px; font-weight: 800; color: var(--green2); margin-bottom: 6px; }
        
        .how { padding: 70px 0 0; }
        .steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
        .steps > div { background: #fff; border: 1px solid var(--line); padding: 24px; border-radius: 20px; }
        .steps b { color: var(--green2); font-size: 12px; }
        .steps h3 { margin: 10px 0 7px; }
        .steps p { margin: 0; color: var(--muted); line-height: 1.5; }
        
        footer { max-width: 1120px; margin: auto; padding: 25px 24px 45px; display: flex; justify-content: space-between; color: var(--muted); font-size: 13px; }
        
        @media(max-width:760px) {
            .hero { grid-template-columns: 1fr; padding: 34px 27px; }
            .plant-art { min-height: 190px; }
            .pot { right: 30px; } .stem { right: 85px; } .leaf1 { right: 60px; } .leaf2 { right: 125px; }
            .card { padding: 22px; }
            .steps { grid-template-columns: 1fr; }
            .section-head h2 { font-size: 25px; }
            h1 { font-size: 42px; }
            footer { flex-direction: column; gap: 8px; }
        }
    </style>
</head>
<body>

    <header class="topbar">
        <a href="#" class="brand">
            <span class="logo">🌿</span>
            <span>Healing the Plant</span>
        </a>
        <div class="lang-switch">
            <button class="active" onclick="setLang('ru')" id="btn-ru">RU</button>
            <button onclick="setLang('kk')" id="btn-kk">KK</button>
            <button onclick="setLang('en')" id="btn-en">EN</button>
        </div>
    </header>

    <main>
        <section class="hero">
            <div>
                <div class="eyebrow" id="txt-eyebrow">ИИ-Помощник Ботаник</div>
                <h1 id="txt-hero-title">Здоровье ваших растений под защитой</h1>
                <p class="heroText" id="txt-hero-desc">Загрузите фотографию листа или стебля, чтобы мгновенно определить диагноз, симптомы болезни и получить точные рекомендации по уходу.</p>
                <div class="heroBadges">
                    <span>⚡ Быстрая оценка</span>
                    <span>🌱 Точный диагноз</span>
                    <span>🛡️ Профилактика</span>
                </div>
            </div>
            <div class="plant-art">
                <div class="sun"></div>
                <div class="stem"></div>
                <div class="leaf leaf1"></div>
                <div class="leaf leaf2"></div>
                <div class="pot"></div>
            </div>
        </section>

        <section class="card">
            <div class="section-head">
                <div>
                    <h2 id="txt-card-title">Диагностика растения</h2>
                    <p style="color: var(--muted); margin-top: 5px;" id="txt-card-sub">Выберите фото или сделайте новый снимок</p>
                </div>
                <span class="ai-chip">GEMINI AI 3.6</span>
            </div>

            <form id="plantForm">
                <div class="actions">
                    <button type="button" class="primary" onclick="document.getElementById('fileInput').click()" id="btn-choose">📁 Выбрать фото</button>
                    <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="handleFileSelect(event)">
                </div>

                <div id="previewBox" class="preview" style="display:none;">
                    <img id="previewImg" src="" alt="Превью">
                    <button type="button" class="remove" onclick="resetFile()">✕</button>
                </div>

                <button type="submit" class="analyze" id="btn-analyze" disabled>Запустить анализ</button>
            </form>

            <div class="loading" id="loading">⏳ <span id="txt-loading">Анализируем фото с помощью ИИ...</span></div>
            <div class="result-text" id="resultBox" style="display:none;"></div>
            <p class="privacy">🔒 Фотографии обрабатываются безопасно и не сохраняются на сервере</p>
        </section>

        <!-- История проверок -->
        <section class="card">
            <div class="section-head">
                <h2 id="txt-history-title">📜 История проверок</h2>
                <button type="button" class="secondary" onclick="clearHistory()" id="btn-clear-hist">Очистить историю</button>
            </div>
            <div id="historyList" style="margin-top: 15px;"></div>
        </section>

        <section class="how">
            <h2 style="font-size: 30px; text-align: center;" id="txt-how-title">Как это работает</h2>
            <div class="steps">
                <div>
                    <b>ШАГ 1</b>
                    <h3 id="txt-s1-t">Загрузка</h3>
                    <p id="txt-s1-d">Сделайте четкое фото поврежденного листа или растения целиком.</p>
                </div>
                <div>
                    <b>ШАГ 2</b>
                    <h3 id="txt-s2-t">ИИ-Анализ</h3>
                    <p id="txt-s2-d">Нейросеть Gemini сканирует симптомы и сравнивает их с базой болезней.</p>
                </div>
                <div>
                    <b>ШАГ 3</b>
                    <h3 id="txt-s3-t">Результат</h3>
                    <p id="txt-s3-d">Получите готовый план лечения и советы по профилактике.</p>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <span>© 2026 Healing the Plant. Все права защищены.</span>
        <span>Разработано с использованием Python & Gemini API</span>
    </footer>

    <script>
        const dict = {
            ru: {
                eyebrow: "ИИ-Помощник Ботаник",
                heroTitle: "Здоровье ваших растений под защитой",
                heroDesc: "Загрузите фотографию листа или стебля, чтобы мгновенно определить диагноз, симптомы болезни и получить точные рекомендации по уходу.",
                cardTitle: "Диагностика растения",
                cardSub: "Выберите фото или сделайте новый снимок",
                choose: "📁 Выбрать фото",
                analyze: "Запустить анализ",
                loading: "Анализируем фото с помощью ИИ...",
                histTitle: "📜 История проверок",
                clearHist: "Очистить историю",
                emptyHist: "История проверок пока пуста",
                howTitle: "Как это работает",
                s1t: "Загрузка", s1d: "Сделайте четкое фото поврежденного листа или растения целиком.",
                s2t: "ИИ-Анализ", s2d: "Нейросеть Gemini сканирует симптомы и сравнивает их с базой болезней.",
                s3t: "Результат", s3d: "Получите готовый план лечения и советы по профилактике."
            },
            kk: {
                eyebrow: "ИИ-Ботаник Көмекші",
                heroTitle: "Өсімдіктеріңіздің денсаулығы қорғауда",
                heroDesc: "Диагнозды, ауру белгілерін бірден анықтау және күтім бойынша дәл ұсыныстар алу үшін жапырақ немесе сабақтың фотосын жүктеңіз.",
                cardTitle: "Өсімдік диагностикасы",
                cardSub: "Фотосуретті таңдаңыз немесе жаңа түсірілім жасаңыз",
                choose: "📁 Фото таңдау",
                analyze: "Талдауды бастау",
                loading: "Фотосурет ИИ арқылы талдануда...",
                histTitle: "📜 Тексеру тарихы",
                clearHist: "Тарихты тазалау",
                emptyHist: "Тексеру тарихы әлі бос",
                howTitle: "Бұл қалай жұмыс істейді",
                s1t: "Жүктеу", s1d: "Зақымдалған жапырақтың немесе өсімдіктің толық анық фотосын түсіріңіз.",
                s2t: "ИИ-Талдау", s2d: "Gemini нейрожелісі белгілерді сканерлеп, аурулар базасымен салыстырады.",
                s3t: "Нәтиже", s3d: "Дайын емдеу жоспарын және алдын алу кеңестерін алыңыз."
            },
            en: {
                eyebrow: "AI Botanist Assistant",
                heroTitle: "Your plants' health is protected",
                heroDesc: "Upload a photo of a leaf or stem to instantly identify the diagnosis, symptoms, and receive accurate care recommendations.",
                cardTitle: "Plant Diagnostics",
                cardSub: "Select a photo or take a new picture",
                choose: "📁 Select Photo",
                analyze: "Start Analysis",
                loading: "Analyzing photo with AI...",
                histTitle: "📜 Inspection History",
                clearHist: "Clear history",
                emptyHist: "History is empty",
                howTitle: "How it works",
                s1t: "Upload", s1d: "Take a clear photo of the damaged leaf or the entire plant.",
                s2t: "AI Analysis", s2d: "Gemini AI scans symptoms and compares them with disease databases.",
                s3t: "Result", s3d: "Get a ready-made treatment plan and prevention tips."
            }
        };

        let currentLang = 'ru';
        let selectedFile = null;

        function setLang(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-switch button').forEach(b => b.classList.remove('active'));
            document.getElementById(`btn-${lang}`).classList.add('active');

            const t = dict[lang];
            document.getElementById('txt-eyebrow').innerText = t.eyebrow;
            document.getElementById('txt-hero-title').innerText = t.heroTitle;
            document.getElementById('txt-hero-desc').innerText = t.heroDesc;
            document.getElementById('txt-card-title').innerText = t.cardTitle;
            document.getElementById('txt-card-sub').innerText = t.cardSub;
            document.getElementById('btn-choose').innerText = t.choose;
            document.getElementById('btn-analyze').innerText = t.analyze;
            document.getElementById('txt-loading').innerText = t.loading;
            document.getElementById('txt-history-title').innerText = t.histTitle;
            document.getElementById('btn-clear-hist').innerText = t.clearHist;
            document.getElementById('txt-how-title').innerText = t.howTitle;
            document.getElementById('txt-s1-t').innerText = t.s1t; document.getElementById('txt-s1-d').innerText = t.s1d;
            document.getElementById('txt-s2-t').innerText = t.s2t; document.getElementById('txt-s2-d').innerText = t.s2d;
            document.getElementById('txt-s3-t').innerText = t.s3t; document.getElementById('txt-s3-d').innerText = t.s3d;
            renderHistory();
        }

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = (event) => {
                    document.getElementById('previewImg').src = event.target.result;
                    document.getElementById('previewBox').style.display = 'block';
                    document.getElementById('btn-analyze').disabled = false;
                };
                reader.readAsDataURL(file);
            }
        }

        function resetFile() {
            selectedFile = null;
            document.getElementById('fileInput').value = '';
            document.getElementById('previewBox').style.display = 'none';
            document.getElementById('btn-analyze').disabled = true;
            document.getElementById('resultBox').style.display = 'none';
        }

        function saveHistory(item) {
            let hist = JSON.parse(localStorage.getItem('plant_hist') || '[]');
            hist.unshift({ date: new Date().toLocaleString(), text: item });
            localStorage.setItem('plant_hist', JSON.stringify(hist));
            renderHistory();
        }

        function renderHistory() {
            const container = document.getElementById('historyList');
            let hist = JSON.parse(localStorage.getItem('plant_hist') || '[]');
            if (hist.length === 0) {
                container.innerHTML = `<p style="color: var(--muted); text-align: center; padding: 15px;">${dict[currentLang].emptyHist}</p>`;
                return;
            }
            container.innerHTML = hist.map(h => `
                <div class="history-item">
                    <div class="history-date">📅 ${h.date}</div>
                    <div style="white-space: pre-line;">${h.text}</div>
                </div>
            `).join('');
        }

        function clearHistory() {
            localStorage.removeItem('plant_hist');
            renderHistory();
        }

        document.getElementById('plantForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);

            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultBox').style.display = 'none';
            document.getElementById('btn-analyze').disabled = true;

            try {
                const res = await fetch('/analyze', { method: 'POST', body: formData });
                const data = await res.json();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('btn-analyze').disabled = false;

                if (res.ok) {
                    const text = data.analysis.replace(/\*\*/g, '');
                    document.getElementById('resultBox').innerText = text;
                    document.getElementById('resultBox').style.display = 'block';
                    saveHistory(text);
                } else {
                    document.getElementById('resultBox').innerText = 'Ошибка: ' + (data.detail || 'Не удалось выполнить анализ');
                    document.getElementById('resultBox').style.display = 'block';
                }
            } catch (err) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('btn-analyze').disabled = false;
                alert('Ошибка соединения с сервером');
            }
        });

        // Инициализация истории при старте
        renderHistory();
    </script>
</body>
</html>
    """

@app.post("/analyze")
async def analyze_plant(file: UploadFile = File(...)):
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "parts": [
                {"text": SYSTEM_INSTRUCTION},
                {
                    "inline_data": {
                        "mime_type": file.content_type or "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }]
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, 
            detail=f"Gemini API Error: {response.text}"
        )

    result = response.json()
    try:
        text_response = result['candidates'][0]['content']['parts'][0]['text']
        return {"analysis": text_response}
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось разобрать ответ от нейросети")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
