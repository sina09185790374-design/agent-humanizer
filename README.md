# agent-humanizer

Make AI-written text read like a careful person wrote it — two passes, stdlib only, no network, no keys. English + Persian.

**Pattern** (original code; pattern only, learned from today's radar): Dodaios/ste80-humanizer rebuilds AI text "80% of the way to ASD-STE100", the controlled English of aircraft maintenance manuals, in two passes — first remove the tells (the 26 signs of AI writing), then rebuild the sentences. This tool is that idea as a small local CLI for both languages we actually write in: it strips the tells *and* rewrites toward controlled English, then proves the improvement with a before/after score. It is the fixer to `slop-guard`'s scorer: one flags AI slop, the other removes it.

## How it works

1. **Pass 1 — strip the tells.** A catalog of stock AI phrases, hedges and filler openers (EN + FA): "in today's fast-paced world", "it's important to note that", "delve", "leverage", "moreover", "could potentially" — and «لازم به ذکر است که», «در دنیای امروز», «بی‌نظیر», «فوق‌العاده», «به طور کلی». Phrases are deleted or replaced with plain words ("leverage" → "use", «بی‌نظیر» → «خوب»).
2. **Pass 2 — rebuild toward controlled English (STE80).** One idea per sentence: sentences over 22 words are split at semicolons, em-dashes and coordinating conjunctions. Safe passives are rewritten to active voice — past ("was written by Sara" → "Sara wrote the report"), future/modal ("will be restarted by the kubelet" → "the kubelet will restart the container"), present for plural subjects ("They are paid by the company" → "The company pays them"). A passive the rewriter cannot conjugate safely is left alone and flagged in the report, never mangled.
3. **Verify.** Every run prints a before/after report: score 0–100, word/sentence counts, average sentence length, tell hits, long sentences, passives, hedges.

## Usage

```bash
python3 -m agent_humanizer humanize draft.txt
python3 -m agent_humanizer humanize --json draft.txt
echo "It's important to note that the cache is full." | python3 -m agent_humanizer humanize

python3 -m agent_humanizer check draft.txt        # score only, no rewrite
# exit 0 when score >= 70, exit 1 below — use it as a CI gate

python3 -m agent_humanizer humanize --strict draft.txt
# exit 1 when any tell survives the rewrite
```

No file (or `-`) reads stdin. Language is detected from the script (Persian characters → FA); both catalogs apply, so mixed text works too.

## Example

Before (score 78/100, 3 tells, 2 long sentences, 1 passive):

> Great question! Kubernetes liveness probes are a powerful mechanism that enables the kubelet to determine whether a container is healthy — and it's not just a health check, it's your first line of defense. When a probe fails, the container will be automatically restarted by the kubelet, ensuring that your application remains available. However, it's important to note that misconfigured probes could potentially cause cascading restarts, so parameters like initialDelaySeconds and failureThreshold should be carefully tuned.

After (score 99/100, 0 tells, 0 long sentences, 0 passives):

> Kubernetes liveness probes are a powerful mechanism that enables the kubelet to determine whether a container is healthy. And it's not just a health check, it's your first line of defense. When a probe fails, the kubelet will restart the container automatically, ensuring that your application remains available. However, misconfigured probes could cause cascading restarts, so parameters like initialDelaySeconds and failureThreshold should be carefully tuned.

Persian, before (score 80/100, 5 tells):

> لازم به ذکر است که در دنیای امروز، این گوشی بی‌نظیر با قابلیت‌های فوق‌العاده خود می‌تواند تجربه‌ای جادویی برای شما رقم بزند.

Persian, after (score 100/100, 0 tells):

> این گوشی خوب با قابلیت‌های خوب خود می‌تواند تجربه‌ای برای شما رقم بزند.

Full verified runs: `examples/before-after.md`.

## Scoring

`score = 100 − 4×tells (capped at 10) − 3×long sentences − 2×passives − hedges − 2 if avg > 22 words/sentence`, floored at 0. "Passives" counts by-phrase passives ("was written by Sara"); a bare passive without "by" is not counted.

## Tests

```bash
python3 -m unittest discover -s tests
# Ran 31 tests — OK (tell removal EN/FA, sentence splitting, passive
# rewrites incl. future/modal/adverb, present-singular left alone,
# idempotency, clean-text no-op, CLI exit codes)
```

The tests caught 2 real bugs before shipping: the present-tense passive rewrite dropped the 3rd-person -s ("The company pay them"), and split long sentences lost their terminating period.

## Why a humanizer, not a detector

Detectors argue about whether a text *is* AI. This tool does not care: it removes the fingerprints and rebuilds the sentences, then measures the result. The goal is text people read easily — the same goal as the STE80 method — not getting past a detector.

---

# agent-humanizer (فارسی)

متن نوشته‌شده با هوش مصنوعی را طوری بازنویسی می‌کند که انگار یک آدم دقیق نوشته است — دو مرحله، فقط استاندارد لایبرری پایتون، بدون اینترنت و بدون کلید. انگلیسی + فارسی.

**الگو** (کد کاملاً اورجینال؛ فقط الگو از رادار امروز): Dodaios/ste80-humanizer متن هوش مصنوعی را «۸۰٪ راه تا ASD-STE100» — انگلیسی کنترل‌شدهٔ دفترچه‌های تعمیر هواپیما — بازسازی می‌کند، در دو مرحله: اول حذف نشانه‌ها (۲۶ نشانهٔ نوشتهٔ هوش مصنوعی)، بعد بازسازی جمله‌ها. این ابزار همان ایده است به شکل یک CLI کوچک برای هر دو زبانی که واقعاً با آن می‌نویسیم: نشانه‌ها را حذف می‌کند *و* جمله‌ها را به سمت انگلیسی کنترل‌شده بازسازی می‌کند، بعد با امتیاز قبل/بعد بهبود را ثابت می‌کند. مکمل `slop-guard` است: آن یکی امتیاز می‌دهد، این یکی اصلاح می‌کند.

## روش کار

۱. **مرحلهٔ اول — حذف نشانه‌ها.** فهرستی از عبارت‌های کلیشه‌ای هوش مصنوعی، تردیدها و شروع‌کننده‌های پرکننده (انگلیسی + فارسی): «in today's fast-paced world»، «it's important to note that»، «delve»، «leverage»، «moreover»، «could potentially» — و «لازم به ذکر است که»، «در دنیای امروز»، «بی‌نظیر»، «فوق‌العاده»، «به طور کلی». عبارت‌ها حذف یا با کلمهٔ ساده جایگزین می‌شوند («leverage» → «use»، «بی‌نظیر» → «خوب»).
۲. **مرحلهٔ دوم — بازسازی به سمت انگلیسی کنترل‌شده (STE80).** یک ایده در هر جمله: جمله‌های بالای ۲۲ کلمه در نقطه‌ویرگول، خط تیره و حروف ربط شکسته می‌شوند. جملات مجهولِ امن به معلوم تبدیل می‌شوند — گذشته («was written by Sara» → «Sara wrote the report»)، آینده/وجهی («will be restarted by the kubelet» → «the kubelet will restart the container»)، حال برای فاعل جمع («They are paid by the company» → «The company pays them»). جملهٔ مجهولی که بازنویسی امن ندارد دست نمی‌خورد و در گزارش علامت می‌خورد، نه اینکه خراب شود.
۳. **سنجش.** هر اجرا گزارش قبل/بعد چاپ می‌کند: امتیاز ۰ تا ۱۰۰، تعداد کلمه و جمله، میانگین طول جمله، نشانه‌ها، جمله‌های طولانی، مجهول‌ها، تردیدها.

## استفاده

```bash
python3 -m agent_humanizer humanize draft.txt
python3 -m agent_humanizer humanize --json draft.txt
echo "It's important to note that the cache is full." | python3 -m agent_humanizer humanize

python3 -m agent_humanizer check draft.txt        # فقط امتیاز، بدون بازنویسی
# خروج ۰ وقتی امتیاز ۷۰ یا بیشتر باشد، خروج ۱ پایین‌تر — برای گیت CI مناسب است

python3 -m agent_humanizer humanize --strict draft.txt
# خروج ۱ وقتی نشانه‌ای بعد از بازنویسی باقی بماند
```

بدون فایل (یا `-`) از stdin می‌خواند. زبان از روی خط متن تشخیص داده می‌شود (حروف فارسی → فارسی)؛ هر دو فهرست اعمال می‌شوند، پس متن مخلوط هم کار می‌کند.

## تست‌ها

```bash
python3 -m unittest discover -s tests
# Ran 31 tests — OK
```

تست‌ها پیش از انتشار ۲ باگ واقعی گرفتند: بازنویسی مجهول حال، ‎-s سوم‌شخص را جا می‌انداخت («The company pay them»)، و جمله‌های طولانیِ شکسته‌شده نقطهٔ پایانی‌شان را از دست می‌دادند.
