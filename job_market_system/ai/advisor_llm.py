"""
ai/advisor_llm.py
-------------------
Generates the personalized career-advice text for the /api/advisor
endpoint using a real local LLM instead of hardcoded string templates.

This replaces the `advice_parts` block inside recommender.analyze_career_ai().
Everything else in that function -- match_score, best_role, matched_skills,
missing_skills, market_salary_range -- is still your existing scoring
logic. Only the *prose generation* moves from f-strings to an LLM. The
frontend (web/index.html) already expects the advice text to contain
"### Heading" lines, "**bold**" spans, and "- bullet" lines, so the
prompt below asks the model to keep using that structure -- no frontend
changes needed.

COST: $0. Runs through Ollama, entirely on your own machine.
SETUP:
    1. Install Ollama: https://ollama.com/download
    2. ollama pull llama3.2        (about 2GB, ~3B params, fine on a laptop CPU)
    3. pip install ollama --break-system-packages
"""

MODEL_NAME = "llama3.2"

ADVISOR_PROMPT = """Bạn là một chuyên gia tư vấn hướng nghiệp ngành IT tại \
Việt Nam. Dựa CHỈ trên các dữ liệu dưới đây (không bịa thêm số liệu hay kỹ \
năng nào khác), hãy viết lời khuyên hướng nghiệp cá nhân hoá, giọng văn tự \
nhiên, khích lệ. Giữ đúng cấu trúc định dạng sau (dùng chính xác các dấu \
### và ** như ví dụ, để giao diện web hiển thị đúng):

### 🎯 Đánh giá mức độ phù hợp: {match_score}%
(1-2 câu đánh giá tổng quan, nhắc đến vai trò **{best_role}** và cấp bậc {level_user})

### 💪 Kỹ năng thế mạnh đã đáp ứng:
- (nhận xét ngắn gọn, tự nhiên về các kỹ năng: {matched_skills})

### 🚀 Kỹ năng nên bổ sung để tăng cạnh tranh:
- (gợi ý cụ thể nên học kỹ năng nào trong số này trước, và vì sao: {missing_skills})

### 💰 Mức lương thị trường dự báo ({level_user} - {best_role}):
- Khoảng lương phổ biến: **{salary_min} - {salary_max} triệu VNĐ/tháng**.
- (1 câu so sánh với mức kỳ vọng {expected_salary} triệu của ứng viên)

### 📅 Lộ trình phát triển 3 tháng đề xuất:
- Tháng 1: (đề xuất cụ thể, dựa trên kỹ năng thế mạnh)
- Tháng 2: (đề xuất cụ thể, dựa trên kỹ năng còn thiếu)
- Tháng 3: (đề xuất chuẩn bị phỏng vấn / portfolio)

Chỉ trả về nội dung theo đúng cấu trúc trên, không thêm lời dẫn hay ghi chú nào khác.
"""


class AdvisorLLMUnavailable(Exception):
    """Raised when the local LLM can't be reached -- callers should catch
    this and fall back to the template-based advice text instead of
    letting the whole /api/advisor request fail."""


def generate_advice_llm(match_score, best_role, level_user, matched_skills,
                         missing_skills, salary_min, salary_max, expected_salary):
    try:
        import ollama
    except ImportError as e:
        raise AdvisorLLMUnavailable("ollama package not installed") from e

    prompt = ADVISOR_PROMPT.format(
        match_score=match_score,
        best_role=best_role,
        level_user=level_user,
        matched_skills=", ".join(matched_skills) if matched_skills else "chưa có kỹ năng nổi bật nào khớp",
        missing_skills=", ".join(missing_skills[:5]) if missing_skills else "không có",
        salary_min=salary_min,
        salary_max=salary_max,
        expected_salary=expected_salary,
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.5},  # some natural variation in phrasing,
                                            # but still grounded in the facts given
        )
    except Exception as e:
        # Covers "Ollama not running", "model not pulled", connection refused, etc.
        # Broad on purpose: any failure here should fall back gracefully rather
        # than break the advisor endpoint for the user.
        raise AdvisorLLMUnavailable(str(e)) from e

    text = response["message"]["content"].strip()
    if not text:
        raise AdvisorLLMUnavailable("empty response from model")
    return text + "\n"
