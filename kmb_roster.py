import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# ==== 使用者帳密設定 ====
login_id = os.environ.get("LOGIN_ID")
login_pw = os.environ.get("LOGIN_PW")

# ==== 啟動瀏覽器 ====
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # 可選：無頭模式
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

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

# 抓取 <td class="row1"> 中第 5 個 <table>
tables = soup.select("td.row1 > table")
if len(tables) >= 5:
    correct_table = tables[4]
else:
    print("❌ 找不到 <td class='row1'> 中的第 5 個 <table>。")
    exit()

# ==== 抽出整個 <table> HTML ====
target_html = str(correct_table)

# ==== 寫入 HTML 頁面 ====
html_template = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>巴士更表預覽</title>
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
  </style>
</head>
<body>
  <h1>龍運羊仔值更時間表</h1>
  {target_html}
</body>
</html>"""

with open("duty_roster.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("✅ 網頁已產生：duty_roster.html")
