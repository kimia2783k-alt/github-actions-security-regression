# کارهایی که شما باید روی GitHub انجام دهید

فایل‌های لازم در پروژه آماده است. فقط این مراحل را انجام دهید.

## ۱) نصب Git (اگر ندارید)

از اینجا نصب کنید: https://git-scm.com/download/win  
بعد ترمینال را ببندید و دوباره باز کنید.

## ۲) ساخت مخزن خالی روی GitHub

1. بروید به https://github.com/new  
2. نام مثلاً: `github-actions-security-regression`  
3. Visibility را **Public** بگذارید  
4. تیک README / LICENSE / gitignore را **نزنید**  
5. Create repository  
6. آدرس را کپی کنید، شبیه:  
   `https://github.com/USERNAME/github-actions-security-regression.git`

## ۳) Push از پوشهٔ پروژه

در PowerShell داخل پوشهٔ `مقاله روش پژوهش`:

```powershell
git init
git add .
git status
```

حتماً چک کنید فایل `.env` در لیست staged نباشد.

```powershell
git commit -m "Initial public release: pin-semantics-v0.5 replication package"
git branch -M main
git remote add origin https://github.com/USERNAME/github-actions-security-regression.git
git push -u origin main
```

`USERNAME` و نام مخزن را با مقدار خودتان عوض کنید.

## ۴) برای مقاله بفرستید

- آدرس عمومی مخزن (بدون `.git`)
- هش کامل آخرین commit (۴۰ کاراکتر)

بعد از آن، آدرس داخل متن مقاله و فایل‌های Word گذاشته می‌شود.

جزئیات بیشتر انگلیسی: `replication/PUBLISH.md`
