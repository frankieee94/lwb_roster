
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# ==== 使用者帳密設定 ====
import os
login_id = os.getenv("LOGIN_ID", "").strip()
login_pw = os.getenv("LOGIN_PW", "").strip()
if not login_id or not login_pw:
    print("❌ LOGIN_ID 或 LOGIN_PW 未設定。請確認 GitHub Secrets。")
    exit()

# ==== 啟動瀏覽器 ====
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
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

# ==== 擷取正確的 <table> ====
soup = BeautifulSoup(html, "html.parser")
tables = soup.select("td.row1 > table")
if len(tables) < 5:
    print("❌ 找不到 <td class='row1'> 中的第 5 個 <table>。")
    exit()

raw_table = tables[4]
all_rows = raw_table.find_all("tr")

# ==== 修改 header 名稱 ====
header_cells = all_rows[0].find_all(["td", "th"])
if len(header_cells) >= 8:
    header_cells[6].string = "簽到地點"
    header_cells[7].string = "出勤狀態"

thead = soup.new_tag("thead")
thead.append(all_rows[0])

today = datetime.now().date()
yesterday = today - timedelta(days=1)

tbody = soup.new_tag("tbody")
for tr in all_rows[1:]:
    cells = tr.find_all("td")
    if cells:
        date_text = cells[0].get_text(strip=True)[:10]  # e.g. 2025/05/11
        try:
            row_date = datetime.strptime(date_text, "%Y/%m/%d").date()
            if row_date == today:
                tr['style'] = "background-color: #FFF6D5;"  # 今日：淡黃色
            elif row_date == yesterday:
                tr['style'] = "background-color: #F2F2F2;"  # 昨日：淡灰色
        except:
            pass  # 若格式錯誤就跳過
    tbody.append(tr)

clean_table = soup.new_tag("table")
clean_table.attrs = raw_table.attrs
clean_table.append(thead)
clean_table.append(tbody)
target_html = str(clean_table)

now_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y/%m/%d %H:%M")

html_template = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="manifest.json">
  <link rel="icon" href="icon192.png">
  <link rel="apple-touch-icon" href="icon192.png">
  <!-- Open Graph (for Facebook, WhatsApp, LinkedIn) -->
  <meta property="og:title" content="龍運羊仔 - 值更時間表">
  <meta property="og:description" content="每日自動更新的龍運車長更表，可篩選出勤狀態、路線、更份等資料。">
  <meta property="og:image" content="https://frankieee94.github.io/lwb_roster/thumbnail.png">
  <meta property="og:url" content="https://frankieee94.github.io/lwb_roster/duty_roster.html">
  <meta property="og:type" content="website">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="龍運羊仔 - 值更時間表">
  <meta name="twitter:description" content="每日自動更新的龍運車長更表，可篩選出勤狀態、路線、更份等資料。">
  <meta name="twitter:image" content="https://frankieee94.github.io/lwb_roster/thumbnail.png">
  <title>龍運 - 羊仔更表</title>
  <style>
    body {{
      font-family: 'PingFang TC', 'Noto Sans TC', sans-serif;
      background-color: #f9f9f9;
      padding: 2rem;
    }}
    .filters {{
      margin-bottom: 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 14px;
    }}
    .filters label {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .filters select {{
      font-size: 14px;
      padding: 3px;
    }}
    .last-update {{
      font-size: 14px;
      color: #666;
      margin-bottom: 1.5rem;
    }}
    .table-container {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background-color: white;
      min-width: 1000px;
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
  <h1>龍運 - 羊仔更表</h1>
  <div class="last-update">最後更新時間(香港)：{now_str}</div>

  <div class="filters">
    <label>編更廠：
      <select id="filter-depot"><option value="">全部</option></select>
    </label>
    <label>路線：
      <select id="filter-route"><option value="">全部</option></select>
    </label>
    <label>字軌：
      <select id="filter-code"><option value="">全部</option></select>
    </label>
    <label>更份：
      <select id="filter-shift"><option value="">全部</option></select>
    </label>
    <label>簽到地點：
      <select id="filter-checkin"><option value="">全部</option></select>
    </label>
    <label>出勤狀態（可多選）：
      <select id="filter-location" multiple size="4"></select>
    </label>
  </div>

  <div class="table-container">
    {target_html}
  </div>

  <script>
    const columnIndexMap = {{
      depot: 1,
      route: 2,
      code: 3,
      shift: 4,
      checkin: 6,
      location: 7
    }};

    function getUniqueColumnValues(index) {{
      const rows = Array.from(document.querySelectorAll("table tbody tr")).slice(1);
      const values = new Set();
      rows.forEach(row => {{
        const cell = row.cells[index];
        if (cell && cell.textContent.trim()) {{
          values.add(cell.textContent.trim());
        }}
      }});
      return Array.from(values).sort();
    }}

    function populateFilter(id, values) {{
      const select = document.getElementById(id);
      values.forEach(val => {{
        const option = document.createElement("option");
        option.value = val;
        option.textContent = val;
        select.appendChild(option);
      }});
    }}

    function getMultiSelectValues(selectElement) {{
      return Array.from(selectElement.selectedOptions).map(opt => opt.value);
    }}

    function applyFilters() {{
      const filters = {{
        depot: document.getElementById("filter-depot").value,
        route: document.getElementById("filter-route").value,
        code: document.getElementById("filter-code").value,
        shift: document.getElementById("filter-shift").value,
        checkin: document.getElementById("filter-checkin").value,
        location: getMultiSelectValues(document.getElementById("filter-location"))
      }};
      const rows = document.querySelectorAll("table tbody tr");
      rows.forEach(row => {{
        let visible = true;
        for (const key in filters) {{
          const val = filters[key];
          const cell = row.cells[columnIndexMap[key]];
          const text = cell ? cell.textContent.trim() : "";

          if (key === "location") {{
            if (val.length && !val.includes(text)) {{
              visible = false;
              break;
            }}
          }} else {{
            if (val && text !== val) {{
              visible = false;
              break;
            }}
          }}
        }}
        row.style.display = visible ? "" : "none";
      }});
    }}

    document.addEventListener("DOMContentLoaded", () => {{
      const keys = ["depot", "route", "code", "shift", "checkin", "location"];
      keys.forEach(key => {{
        const filterId = "filter-" + key;
        const values = getUniqueColumnValues(columnIndexMap[key]);
        populateFilter(filterId, values);
        document.getElementById(filterId).addEventListener("change", applyFilters);
      }});
    }});
  </script>
</body>
</html>
"""

with open("duty_roster.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("✅ 已輸出 duty_roster.html，支援多選出勤狀態")
