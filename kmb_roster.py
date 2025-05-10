import os
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ==== 使用者帳密設定 ====
login_id = os.environ.get("LOGIN_ID")
login_pw = os.environ.get("LOGIN_PW")

if not login_id or not login_pw:
    print("❌ LOGIN_ID 或 LOGIN_PW 未設定。請確認 GitHub Secrets。")
    exit(1)

# ==== 啟動瀏覽器（Headless for GitHub Actions） ====
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ==== 直接開啟 dutyroster 頁面，會自動導向登入頁 ====
driver.get("https://www.kmb.org.hk/kmbhr/drs/dutyroster.php")
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
driver.find_element(By.NAME, "username").send_keys(login_id)
driver.find_element(By.NAME, "password").send_keys(login_pw)
driver.find_element(By.XPATH, "//input[@type='submit' and @value='  確定  ']").click()

# ==== 等更表頁面載入完成 ====
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table//tr")))
html = driver.page_source
driver.quit()

# ==== 解析排班表格，擷取正確層級的 <table> HTML 區段 ====
soup = BeautifulSoup(html, "html.parser")
tables = soup.select("td.row1 > table")
if len(tables) >= 5:
    correct_table = tables[4]
else:
    print("❌ 找不到 <td class='row1'> 中的第 5 個 <table>。")
    exit()

target_html = str(correct_table)

# ==== 顯示最後更新時間（轉為香港時間 UTC+8） ====
hkt = timezone(timedelta(hours=8))
now_str = datetime.now(hkt).strftime("%Y-%m-%d %H:%M:%S")

# ==== 寫入 HTML 頁面 ====
html_template = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>龍運羊仔 - 值更時間表</title>
  <style>
    body {{
      font-family: 'PingFang TC', 'Noto Sans TC', sans-serif;
      background-color: #f9f9f9;
      padding: 2rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background-color: white;
    }}
    td, th {{
      border: 1px solid #ccc;
      padding: 6px;
      font-size: 14px;
      text-align: center;
    }}
    .note {{
      margin-top: 1rem;
      font-size: 12px;
      color: #555;
    }}
  </style>
</head>
<body>
  <h1>龍運羊仔 - 值更時間表</h1>
  <div class=\"note\">最後更新時間（香港）：{now_str}</div>
  {target_html}
  <script>
    const CHECK_INTERVAL = 900000; // 每 15 分鐘
    let lastModified = null;

    async function checkForUpdate() {{
      try {{
        const response = await fetch(window.location.href, {{
          method: 'HEAD',
          cache: 'no-store'
        }});
        const newModified = response.headers.get('last-modified');
        if (lastModified && newModified && newModified !== lastModified) {{
          document.getElementById("update-notice").style.display = "block";
          setTimeout(() => location.reload(true), 3000);
        }}
        lastModified = newModified;
      }} catch (err) {{
        console.error("🔁 檢查更新失敗:", err);
      }}
    }}

    checkForUpdate();
    setInterval(checkForUpdate, CHECK_INTERVAL);
  </script>
</body>
</html>"""

with open("duty_roster.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("✅ 網頁已產生：duty_roster.html")
