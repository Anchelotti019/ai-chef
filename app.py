import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
from PIL import Image
from datetime import datetime
import base64

# ===== НАСТРОЙКА СТРАНИЦЫ =====
st.set_page_config(
    page_title="AI-Шеф 🍳",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== КУЛИНАРНЫЙ ДИЗАЙН =====
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #FFF8F0 0%, #FFE8D6 100%);
    }
    h1 { color: #D2691E !important; font-weight: bold !important; }
    h2, h3 { color: #8B4513 !important; }
    
    .hero-box {
        background: linear-gradient(135deg, #FF8C42 0%, #FFA630 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(255, 140, 66, 0.3);
    }
    .hero-box h1 { color: white !important; margin: 0; font-size: 3em; }
    .hero-box p { color: rgba(255,255,255,0.9); font-size: 1.2em; margin-top: 10px; }
    
    .recipe-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 5px solid #FF8C42;
    }
    
    .photo-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    .info-box {
        background: #FFF3CD;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FFA630;
        margin: 15px 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #FF8C42 0%, #FFA630 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 30px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ===== ИНИЦИАЛИЗАЦИЯ ИСТОРИИ =====
if "recipes" not in st.session_state:
    st.session_state.recipes = []

# ===== ЗАГРУЗКА КЛЮЧА =====
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ API ключ не найден! Проверь файл .env")
    st.stop()

client = genai.Client(api_key=api_key)

# ===== ШАПКА =====
st.markdown("""
<div class="hero-box">
    <h1>🍳 AI-Шеф</h1>
    <p>Загрузи фото холодильника — получи рецепт и фото блюда!</p>
</div>
""", unsafe_allow_html=True)

# ===== БОКОВАЯ ПАНЕЛЬ =====
with st.sidebar:
    st.header("⚙️ Настройки рецепта")
    
    cuisine = st.selectbox(
        "🌍 Кухня мира:",
        ["Любая", "Итальянская 🇮🇹", "Азиатская 🥢", "Русская 🇷🇺", 
         "Мексиканская 🌮", "Французская 🥐", "Грузинская 🍇"]
    )
    portions = st.slider("👥 Количество порций:", 1, 10, 2)
    
    st.divider()
    st.subheader("🥗 Фильтры:")
    vegetarian = st.checkbox("🌱 Вегетарианское")
    quick = st.checkbox("⚡ Быстрое (до 20 минут)")
    diet = st.checkbox("🥦 Диетическое")
    
    st.divider()
    generate_photo = st.toggle("🎨 Генерировать фото блюда", value=False)
    
    st.divider()
    st.metric("📜 Рецептов создано:", len(st.session_state.recipes))
    
    st.divider()
    with st.expander("🆘 Помощь при ошибках"):
        st.markdown("""
        **Лимит 429 исчерпан?**
        
        1. Зайди на [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
        2. Нажми "Create API key in **new project**"
        3. Скопируй ключ
        4. Вставь в `.env`
        5. Перезапусти приложение
        """)

# ===== ОСНОВНАЯ ОБЛАСТЬ =====
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📸 Твоё фото")
    uploaded_file = st.file_uploader("Перетащи фото сюда", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)

with col2:
    st.subheader("🍽️ Результат")
    
    if uploaded_file is not None:
        if st.button("👨‍🍳 Сгенерировать рецепт", type="primary", use_container_width=True):
            
            # ШАГ 1: Распознаём продукты (с обработкой ошибок)
            products = None
            try:
                with st.spinner("🤖 Нейросеть изучает продукты..."):
                    prompt1 = """
                    Посмотри на фото и перечисли ВСЕ продукты питания.
                    Если продуктов нет, ответь: НЕТ_ПРОДУКТОВ
                    Если есть — списком с дефисами.
                    """
                    response1 = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[img, prompt1]
                    )
                    products = response1.text.strip()
            except Exception as e:
                error_text = str(e)
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    st.error("🚫 Дневной лимит запросов исчерпан!")
                    st.markdown("""
                    <div class="info-box">
                    <b>Что делать:</b>
                    <ol>
                        <li>Зайди на <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a></li>
                        <li>Нажми "Create API key in <b>new project</b>"</li>
                        <li>Скопируй новый ключ</li>
                        <li>Открой файл <code>.env</code> в папке проекта</li>
                        <li>Замени старый ключ на новый</li>
                        <li>Останови приложение (Ctrl+C) и запусти снова: <code>streamlit run app.py</code></li>
                    </ol>
                    💡 Бесплатный лимит — 20 запросов в день на проект.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Ошибка распознавания: {error_text[:200]}")
            
            # Продолжаем только если продукты получены
            if products:
                if "НЕТ_ПРОДУКТОВ" in products.upper():
                    st.warning("🤔 На фото не найдены продукты!")
                    st.info("💡 Попробуй фото с содержимым холодильника.")
                else:
                    with st.expander("📋 Найденные продукты", expanded=True):
                        st.markdown(products)
                    
                    # Настройки рецепта
                    settings = []
                    if cuisine != "Любая":
                        settings.append(f"Кухня: {cuisine}")
                    settings.append(f"Порций: {portions}")
                    if vegetarian: settings.append("Вегетарианское блюдо")
                    if quick: settings.append("Время приготовления: до 20 минут")
                    if diet: settings.append("Диетическое блюдо")
                    settings_text = "\n".join(settings)
                    
                    # ШАГ 2: Генерируем рецепт
                    recipe = None
                    try:
                        with st.spinner("👨‍🍳 Шеф-повар придумывает блюдо..."):
                            prompt2 = f"""
                            Продукты: {products}
                            
                            Требования:
                            {settings_text}
                            
                            Придумай рецепт. В ПЕРВОЙ СТРОКЕ напиши ТОЛЬКО название блюда 
                            (без эмодзи, без лишних слов). Например: "Паста карбонара"
                            
                            Затем в формате:
                            ⏱️ Время: X мин | 👥 Порций: {portions}
                            
                            📦 **Ингредиенты:**
                            - список
                            
                            👨‍🍳 **Приготовление:**
                            1. Шаги
                            
                            💡 **Совет шефа:** совет
                            """
                            response2 = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=[prompt2]
                            )
                            recipe = response2.text
                    except Exception as e:
                        error_text = str(e)
                        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                            st.error("🚫 Дневной лимит запросов исчерпан!")
                            st.markdown("""
                            <div class="info-box">
                            <b>Что делать:</b>
                            <ol>
                                <li>Зайди на <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a></li>
                                <li>Нажми "Create API key in <b>new project</b>"</li>
                                <li>Скопируй новый ключ</li>
                                <li>Открой файл <code>.env</code> в папке проекта</li>
                                <li>Замени старый ключ на новый</li>
                                <li>Останови приложение (Ctrl+C) и запусти снова</li>
                            </ol>
                            💡 Бесплатный лимит — 20 запросов в день на проект.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"❌ Ошибка генерации рецепта: {error_text[:200]}")
                    
                    # Продолжаем только если рецепт получен
                    if recipe:
                        # Извлекаем название блюда
                        dish_name = recipe.split('\n')[0].strip().replace('🍽️', '').replace('**', '').strip()
                        
                        # Показываем рецепт
                        st.markdown(f'<div class="recipe-card">{recipe}</div>', unsafe_allow_html=True)
                        
                        # ШАГ 3: Генерируем фото (если включено)
                        generated_image = None
                        if generate_photo and dish_name:
                            with st.spinner("🎨 Художник рисует блюдо... (10-30 сек)"):
                                try:
                                    photo_prompt = f"""
                                    Professional food photography of {dish_name}. 
                                    Beautiful plate, restaurant lighting, top view, 
                                    appetizing, high quality, photorealistic.
                                    """
                                    
                                    photo_response = client.models.generate_content(
                                        model="gemini-2.5-flash-image",
                                        contents=[photo_prompt]
                                    )
                                    
                                    for part in photo_response.candidates[0].content.parts:
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            generated_image = part.inline_data.data
                                            break
                                            
                                except Exception as e:
                                    error_text = str(e)
                                    
                                    if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower():
                                        st.warning("⚠️ Лимит генерации фото исчерпан!")
                                        st.info("💡 Бесплатный тариф позволяет ~10 фото в день. Попробуй завтра.")
                                    elif "404" in error_text or "not found" in error_text.lower():
                                        st.warning("⚠️ Модель генерации изображений недоступна!")
                                        st.info("💡 Рецепт работает без фото.")
                                    else:
                                        st.warning(f"⚠️ Ошибка генерации: {error_text[:100]}")
                                    
                                    generated_image = None
                        
                        # Показываем фото, если получилось
                        if generated_image:
                            st.markdown("### 📷 Фото твоего блюда:")
                            image_base64 = base64.b64encode(generated_image).decode()
                            st.markdown(
                                f'<div class="photo-card"><img src="data:image/png;base64,{image_base64}" style="width:100%; border-radius:10px;"/></div>',
                                unsafe_allow_html=True
                            )
                            st.download_button(
                                "🖼️ Скачать фото блюда",
                                data=generated_image,
                                file_name=f"{dish_name[:20]}.png",
                                mime="image/png"
                            )
                        
                        # Сохраняем в историю
                        st.session_state.recipes.append({
                            "time": datetime.now().strftime("%H:%M"),
                            "cuisine": cuisine,
                            "recipe": recipe,
                            "has_photo": generated_image is not None
                        })
                        
                        st.success("✅ Рецепт готов! Приятного аппетита!")
    else:
        st.info("📸 Сначала загрузи фото продуктов слева!")

# ===== ИСТОРИЯ =====
st.divider()
if st.session_state.recipes:
    st.header("📜 История рецептов")
    for i, item in enumerate(reversed(st.session_state.recipes), 1):
        photo_icon = "📸" if item.get('has_photo') else ""
        with st.expander(f"🍳 Рецепт #{len(st.session_state.recipes) - i + 1} ({item['cuisine']}, {item['time']}) {photo_icon}"):
            st.markdown(item["recipe"])