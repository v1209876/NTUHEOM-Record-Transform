import assemblyai as aai
import google.generativeai as genai
import streamlit as st
import tempfile
import os

# 1. 設定 API Keys (請保留雙引號，將字串替換為你的真實 Key)
aai.settings.api_key = st.secrets["ASSEMBLYAI_KEY"]
aai.settings.http_timeout = 600.0
genai.configure(api_key=st.secrets["GEMINI_KEY"])

# 2. 核心功能：語音轉文字與語者辨識 (已補上 HIPAA 醫療級資安遮蔽)
def transcribe_audio(file_path):
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"],
        speaker_labels=True,
        language_code="zh",
        # ⚠️ 醫院專用版絕對不能漏掉以下兩行
        redact_pii=True,
        redact_pii_policies=[aai.PIIRedactionPolicy.person_name, aai.PIIRedactionPolicy.medical_condition, aai.PIIRedactionPolicy.medical_process]
    )
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        return f"語音辨識發生錯誤: {transcript.error}"

    formatted_text = ""
    for utterance in transcript.utterances:
        formatted_text += f"講者 {utterance.speaker}: {utterance.text}\n"
    return formatted_text


# 3. 核心功能：專業研討會摘要生成
def generate_medical_summary(transcript_text):
    # 無縫升級至更新、更強大的 Gemini 2.5 Flash 模型
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 針對專業醫學與研討會場景最佳化的 Prompt
    prompt = f"""
    你是一位專業的醫學秘書。這是一份專業醫學報告或臨床研討會的逐字稿。
    請根據內容，提供以下結構化資訊：
    1. 核心摘要（請精準保留醫學術語、臨床數據、疾病名稱與處置建議）
    2. 臨床或行政待辦事項（Action Items，例如：後續追蹤檢查、介入建議、復工評估安排等），並盡可能指出負責的講者或單位。

    逐字稿內容：
    {transcript_text}
    """
    response = model.generate_content(prompt)
    return response.text


# 4. Streamlit 網頁介面設計
st.set_page_config(page_title="會議逐字稿與摘要系統", page_icon="🩺")
st.title("🩺 高效會議逐字稿與摘要系統")
# 建立專屬品牌與密碼牆
st.markdown("### ⚡️ 台大醫院環境及職業醫學部專用")
st.caption("Powered by Dr.謝秉高")

# 設定你的專屬密碼
SECRET_PASSWORD = st.secrets["APP_PASSWORD"]

# 密碼輸入框
user_password = st.text_input("請輸入系統授權碼：", type="password")

if user_password != SECRET_PASSWORD:
    st.warning("請輸入正確的授權碼以解鎖系統。")
    st.stop() # 密碼錯誤時，強制停止執行下方的所有程式碼

st.success("授權成功！歡迎使用。")
# --- 下方保留原本的 uploaded_file = st.file_uploader(...) 等程式碼 ---


uploaded_file = st.file_uploader("請上傳會議音檔 (支援 mp3, wav, m4a)", type=['mp3', 'wav', 'm4a'])

if uploaded_file is not None:
    if st.button("開始處理"):
        # 區塊 1：處理音檔
        with st.spinner("正在辨識語音與講者...（1小時音檔約需幾分鐘，請耐心等候）"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            transcript_result = transcribe_audio(tmp_file_path)

            st.subheader("📝 會議逐字稿")
            st.text_area("完整內容", transcript_result, height=300)

        # 區塊 2：生成摘要
        with st.spinner("正在生成專業摘要與待辦事項..."):
            summary_result = generate_medical_summary(transcript_result)

            st.subheader("💡 摘要與待辦事項")
            st.markdown(summary_result)

        # 清理暫存檔
        os.remove(tmp_file_path)
        st.success("處理完成！")