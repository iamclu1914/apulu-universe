@echo off
REM ============================================================
REM Vawn Research Company — Windows Task Scheduler Setup
REM Run this as Administrator to create all scheduled tasks.
REM Removes old tasks first to prevent overlaps.
REM ============================================================

set PYTHON=C:\Users\rdyal\AppData\Local\Programs\Python\Python312\python.exe
set VAWN_DIR=C:\Users\rdyal\Vawn

echo.
echo === Removing old overlapping tasks ===
echo.

REM Remove old root-level tasks (the original ones)
schtasks /delete /tn "Vawn Morning Post" /f 2>nul
schtasks /delete /tn "Vawn Midday Post" /f 2>nul
schtasks /delete /tn "Vawn Evening Post" /f 2>nul
schtasks /delete /tn "Vawn_HashtagScan" /f 2>nul
echo [OK] Old root-level tasks removed

REM Remove old Vawn\ subfolder tasks if they exist
schtasks /delete /tn "Vawn\ResearchCompany" /f 2>nul
schtasks /delete /tn "Vawn\LyricCardAgent" /f 2>nul
schtasks /delete /tn "Vawn\VideoAgent" /f 2>nul
schtasks /delete /tn "Vawn\VideoAgentCinematic" /f 2>nul
schtasks /delete /tn "Vawn\EngagementAgent" /f 2>nul
schtasks /delete /tn "Vawn\HashtagScan" /f 2>nul
schtasks /delete /tn "Vawn\MorningPost" /f 2>nul
schtasks /delete /tn "Vawn\MiddayPost" /f 2>nul
schtasks /delete /tn "Vawn\EveningPost" /f 2>nul
schtasks /delete /tn "Vawn\MorningEarly" /f 2>nul
schtasks /delete /tn "Vawn\MorningMain" /f 2>nul
schtasks /delete /tn "Vawn\MiddayEarly" /f 2>nul
schtasks /delete /tn "Vawn\MiddayMain" /f 2>nul
schtasks /delete /tn "Vawn\EveningEarly" /f 2>nul
schtasks /delete /tn "Vawn\EveningMain" /f 2>nul
schtasks /delete /tn "Vawn\TextPostMorning" /f 2>nul
schtasks /delete /tn "Vawn\TextPostAfternoon" /f 2>nul
schtasks /delete /tn "Vawn\EngagementBot" /f 2>nul
schtasks /delete /tn "Vawn\AnalyticsDigest" /f 2>nul
schtasks /delete /tn "Vawn\RecycleAgent" /f 2>nul
schtasks /delete /tn "Vawn\LyricAnnotation" /f 2>nul
schtasks /delete /tn "Vawn\MetricsAgent" /f 2>nul
schtasks /delete /tn "Vawn\PipelineDiscovery" /f 2>nul
schtasks /delete /tn "Vawn\PipelineIdeation" /f 2>nul
schtasks /delete /tn "Vawn\Bridge" /f 2>nul
schtasks /delete /tn "Vawn\PromptResearchReddit" /f 2>nul
schtasks /delete /tn "Vawn\PromptResearchVideo" /f 2>nul
echo [OK] Old tasks removed

echo.
echo === Creating unified task schedule ===
echo.

REM === PIPELINE (Apulu Universe — runs before Vawn research) ===

REM 0a. Pipeline Discovery — 5:30am daily (Apify scrape: X, IG, TikTok, Reddit)
schtasks /create /tn "Vawn\PipelineDiscovery" /tr "\"%PYTHON%\" \"C:\Users\rdyal\Apulu Universe\pipeline\discovery\run_all.py\" --project vawn --skip youtube" /sc daily /st 05:30 /f
echo [OK] PipelineDiscovery — 5:30am daily (Apify scrape)

REM 0b. Pipeline Ideation — 5:50am daily (competitive analysis + 7 ideas)
schtasks /create /tn "Vawn\PipelineIdeation" /tr "\"%PYTHON%\" \"C:\Users\rdyal\Apulu Universe\pipeline\ideation\ideation_engine.py\" --project vawn" /sc daily /st 05:50 /f
echo [OK] PipelineIdeation — 5:50am daily (ideation)

REM === VAWN RESEARCH (existing) ===

REM 1. Enhanced Hashtag Scan — 6:00am daily (APU-122: upgraded to enhanced scanner)
schtasks /create /tn "Vawn\HashtagScan" /tr "\"%PYTHON%\" \"%VAWN_DIR%\src\enhanced_scan_hashtags.py\"" /sc daily /st 06:00 /f
echo [OK] Enhanced HashtagScan — 6:00am daily (performance analytics + brand intelligence)

REM 2. Research Company — 6:10am daily
schtasks /create /tn "Vawn\ResearchCompany" /tr "\"%PYTHON%\" \"%VAWN_DIR%\research_company.py\"" /sc daily /st 06:10 /f
echo [OK] ResearchCompany — 6:10am daily

REM 2b. Bridge — 6:25am daily (merges pipeline intel into Vawn daily_brief)
schtasks /create /tn "Vawn\Bridge" /tr "\"%PYTHON%\" \"C:\Users\rdyal\Apulu Universe\pipeline\bridge.py\"" /sc daily /st 06:25 /f
echo [OK] Bridge — 6:25am daily (pipeline -> Vawn)

REM 3. Lyric Card Agent — 6:30am daily
schtasks /create /tn "Vawn\LyricCardAgent" /tr "\"%PYTHON%\" \"%VAWN_DIR%\lyric_card_agent.py\"" /sc daily /st 06:30 /f
echo [OK] LyricCardAgent — 6:30am daily

REM 4. Video Agent (Ken Burns) — 6:45am daily
schtasks /create /tn "Vawn\VideoAgent" /tr "\"%PYTHON%\" \"%VAWN_DIR%\video_agent.py\"" /sc daily /st 06:45 /f
echo [OK] VideoAgent daily — 6:45am

REM 4b. Metrics Agent — 7:00am daily (pull yesterday's engagement, feed into image scoring)
schtasks /create /tn "Vawn\MetricsAgent" /tr "\"%PYTHON%\" \"%VAWN_DIR%\metrics_agent.py\"" /sc daily /st 07:00 /f
echo [OK] MetricsAgent — 7:00am daily

REM === MORNING SLOT (staggered) ===
REM 5a. Morning Early — 8:00am (X + Bluesky — early news cycle)
schtasks /create /tn "Vawn\MorningEarly" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron morning --platforms x,bluesky" /sc daily /st 08:00 /f
echo [OK] MorningEarly — 8:00am (X + Bluesky)

REM 5b. Morning Main — 9:15am (TikTok + Instagram + Threads)
schtasks /create /tn "Vawn\MorningMain" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron morning --platforms tiktok,instagram,threads" /sc daily /st 09:15 /f
echo [OK] MorningMain — 9:15am (TikTok + IG + Threads)

REM === MIDDAY SLOT (staggered) ===
REM 6a. Midday Early — 12:00pm (X + Bluesky — lunch break)
schtasks /create /tn "Vawn\MiddayEarly" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron midday --platforms x,bluesky" /sc daily /st 12:00 /f
echo [OK] MiddayEarly — 12:00pm (X + Bluesky)

REM 6b. Midday Main — 12:45pm (TikTok + Instagram carousel + Threads)
schtasks /create /tn "Vawn\MiddayMain" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron midday --platforms tiktok,instagram,threads" /sc daily /st 12:45 /f
echo [OK] MiddayMain — 12:45pm (TikTok + IG + Threads)

REM === EVENING SLOT (staggered) ===
REM 7a. Evening Early — 6:00pm (X + Bluesky + Instagram slideshow Reel — after work)
schtasks /create /tn "Vawn\EveningEarly" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron evening --platforms x,bluesky,instagram --slideshow" /sc daily /st 18:00 /f
echo [OK] EveningEarly — 6:00pm (X + Bluesky + IG slideshow Reel)

REM 7b. Evening Main — 8:15pm (TikTok + Threads)
schtasks /create /tn "Vawn\EveningMain" /tr "\"%PYTHON%\" \"%VAWN_DIR%\post_vawn.py\" --cron evening --platforms tiktok,threads" /sc daily /st 20:15 /f
echo [OK] EveningMain — 8:15pm (TikTok + Threads)

REM === TEXT-ONLY POSTS (X, Threads, Bluesky — between image slots) ===
REM 8a. Text post morning — 10:30am
schtasks /create /tn "Vawn\TextPostMorning" /tr "\"%PYTHON%\" \"%VAWN_DIR%\text_post_agent.py\"" /sc daily /st 10:30 /f
echo [OK] TextPostMorning — 10:30am (X + Threads + Bluesky text-only)

REM 8b. Text post afternoon — 3:30pm
schtasks /create /tn "Vawn\TextPostAfternoon" /tr "\"%PYTHON%\" \"%VAWN_DIR%\text_post_agent.py\"" /sc daily /st 15:30 /f
echo [OK] TextPostAfternoon — 3:30pm (X + Threads + Bluesky text-only)

REM === ENGAGEMENT ===
REM 9. Comment monitoring — every 2 hours
schtasks /create /tn "Vawn\EngagementAgent" /tr "\"%PYTHON%\" \"%VAWN_DIR%\engagement_agent.py\"" /sc daily /st 08:00 /ri 120 /du 24:00 /f
echo [OK] EngagementAgent — every 2 hours

REM 10. Proactive Bluesky engagement — after each posting slot
schtasks /create /tn "Vawn\EngagementBot" /tr "\"%PYTHON%\" \"%VAWN_DIR%\engagement_bot.py\"" /sc daily /st 09:30 /ri 300 /du 24:00 /f
echo [OK] EngagementBot — 9:30am, 2:30pm, 8:30pm (Bluesky likes/follows)

REM === WEEKLY ===
REM 11. Video Agent (Cinematic) — Sunday 7:00am
schtasks /create /tn "Vawn\VideoAgentCinematic" /tr "\"%PYTHON%\" \"%VAWN_DIR%\video_agent.py\" --cinematic" /sc weekly /d SUN /st 07:00 /f
echo [OK] VideoAgent cinematic — Sunday 7:00am

REM 12. Analytics Digest — Sunday 9:00am
schtasks /create /tn "Vawn\AnalyticsDigest" /tr "\"%PYTHON%\" \"%VAWN_DIR%\analytics_agent.py\"" /sc weekly /d SUN /st 09:00 /f
echo [OK] AnalyticsDigest — Sunday 9:00am

REM 13. Post Recycling — Sunday 2:00pm
schtasks /create /tn "Vawn\RecycleAgent" /tr "\"%PYTHON%\" \"%VAWN_DIR%\recycle_agent.py\"" /sc weekly /d SUN /st 14:00 /f
echo [OK] RecycleAgent — Sunday 2:00pm

REM 14. Lyric Annotation — Wednesday 10:00am
schtasks /create /tn "Vawn\LyricAnnotation" /tr "\"%PYTHON%\" \"%VAWN_DIR%\lyric_annotation_agent.py\"" /sc weekly /d WED /st 10:00 /f
echo [OK] LyricAnnotation — Wednesday 10:00am

REM === PROMPT RESEARCH (Apulu Prompt Generator — 2x/week) ===

REM 15. Prompt Research Reddit — Monday + Thursday 6:00am
schtasks /create /tn "Vawn\PromptResearchReddit" /tr "\"%PYTHON%\" \"C:\Users\rdyal\Apulu Universe\pipeline\prompt-research\run_prompt_research.py\" --only reddit" /sc weekly /d MON,THU /st 06:00 /f
echo [OK] PromptResearchReddit — Mon+Thu 6:00am

REM 16. Prompt Research Video Quality — Wednesday 6:00am
schtasks /create /tn "Vawn\PromptResearchVideo" /tr "\"%PYTHON%\" \"C:\Users\rdyal\Apulu Universe\pipeline\prompt-research\run_prompt_research.py\" --only video" /sc weekly /d WED /st 06:00 /f
echo [OK] PromptResearchVideo — Wed 6:00am

echo.
echo === Complete schedule (22 tasks under Vawn\) ===
echo.
echo   PIPELINE (5:30-5:50am):
echo   5:30am  PipelineDiscovery (Apify: X, IG, TikTok, Reddit)
echo   5:50am  PipelineIdeation (competitive analysis + 7 ideas)
echo.
echo   PREP (6:00-7:00am):
echo   6:00am  HashtagScan
echo   6:10am  ResearchCompany
echo   6:25am  Bridge (merges pipeline intel into daily_brief)
echo   6:30am  LyricCardAgent (4 visual templates)
echo   6:45am  VideoAgent
echo   7:00am  MetricsAgent (pull engagement, score images)
echo.
echo   MORNING:
echo   8:00am  X + Bluesky (image + caption)
echo   9:15am  TikTok + IG Reel + Threads (image + audio)
echo   9:30am  Bluesky engagement bot (likes/follows)
echo  10:30am  Text-only post (X + Threads + Bluesky)
echo.
echo   MIDDAY:
echo  12:00pm  X + Bluesky (image + caption)
echo  12:45pm  TikTok + IG Reel + Threads (image + audio)
echo.
echo   AFTERNOON:
echo   3:30pm  Text-only post (X + Threads + Bluesky)
echo.
echo   EVENING:
echo   6:00pm  X + Bluesky + IG slideshow Reel (5 photos + audio)
echo   8:15pm  TikTok + Threads
echo.
echo   ONGOING:
echo   Every 2h  Comment monitoring (EngagementAgent)
echo   Every 5h  Bluesky engagement bot
echo.
echo   WEEKLY:
echo   Sun 7am   Cinematic video (Higgsfield)
echo   Sun 9am   Analytics digest
echo   Sun 2pm   Post recycling (best of 30+ days ago)
echo   Wed 10am  Lyric annotation Reel
echo.
echo   Instagram Stories auto-repost after every IG Reel.
echo   Hashtag rotation engine prevents shadowbans.
echo   Smart CTA rotation on every post.
echo   Engagement-weighted image selection (feedback loop).
echo   X long-form threads at 3:30pm.
echo   4 lyric card visual templates rotating daily.
echo   24 tasks. Fully autonomous. Self-improving.
echo   Pipeline bridge feeds cross-platform intel into posting system.
echo   Prompt research runs 2x/week for AI video prompt intelligence.
echo.
pause
