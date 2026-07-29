# Job Market Intelligence System

He thong phan tich thi truong viec lam IT Viet Nam. Chi can mot server Python FastAPI duy nhat de chay ca backend (API) va frontend (HTML thuan). Du lieu duoc tu dong thu thap ngay khi khoi dong web.

## Cai dat

```
pip install -r requirements.txt
```

## Chay web app (1 server duy nhat)

```
uvicorn api:app --reload
```

Mo trinh duyet tai http://127.0.0.1:8000

Khi server khoi dong, no se tu dong chay thu thap du lieu o luong nen. Trang web hien thanh trang thai "Dang thu thap..." va tu dong lam moi khi hoan tat. Co the bam nut "Thu thap lai" de cap nhat bat ky luc nao.

## Cac trang tuyen dung duoc ho tro

- ITviec
- VietnamWorks
- CareerViet
- CareerLink

Kien truc OOP: lop truu tuong `BaseJobScraper` trong `scrapers.py`, moi trang ke thua va trien khai `list_url` va `parse` (da hinh). Thu thap nhieu trang chay song song bang multi-threading. Khong dung Selenium; chi dung `requests` + `BeautifulSoup`, va doc JSON nhung trong HTML cho cac trang render bang JavaScript.

Neu khong co mang, he thong tu dong dung lai HTML da luu trong `data/raw_html` lam du phong.

## Cap nhat du lieu bang dong lenh (tuy chon)

```
python fetch.py
python main.py
```

`fetch.py` tai HTML that ve `data/raw_html`. `main.py` thu thap, xu ly, ghi `data/jobs.db`, xuat CSV/JSON va bao cao markdown trong `data/reports`, ve bieu do trong `data/charts`.

## Kiem thu

```
python tests.py
```
