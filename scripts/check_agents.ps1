# Diagnostic & Health Check for Multi-Model Orchestrator-Operator Setup
$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       MULTI-AGENT ENVIRONMENT & HEALTH AUDIT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check LM Studio
Write-Host "`n[1/4] Checking Local LM Studio..." -ForegroundColor Yellow
try {
    $lmsResponse = Invoke-RestMethod -Uri "http://localhost:1234/v1/models" -Method Get -TimeoutSec 3
    Write-Host "  [OK] LM Studio Server is ONLINE (port 1234)" -ForegroundColor Green
    
    $loadedModels = $lmsResponse.data | ForEach-Object { $_.id }
    Write-Host "  Available Models in LM Studio:" -ForegroundColor Gray
    foreach ($m in $loadedModels) {
        Write-Host "   - $m" -ForegroundColor White
    }

    # Test Qwen inference latency
    Write-Host "  Testing quick inference with huihui-qwen3.8-27b-abliterated..." -ForegroundColor Gray
    $t0 = Get-Date
    $testBody = @{
        model = "huihui-qwen3.8-27b-abliterated"
        messages = @(@{ role = "user"; content = "Say OK" })
        max_tokens = 5
    } | ConvertTo-Json
    
    $res = Invoke-RestMethod -Uri "http://localhost:1234/v1/chat/completions" -Method Post -ContentType "application/json" -Body $testBody -TimeoutSec 30
    $elapsed = ((Get-Date) - $t0).TotalMilliseconds
    $reply = $res.choices[0].message.content.Trim()
    Write-Host "  [OK] Local Model Responded: '$reply' in $([math]::Round($elapsed))ms" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] LM Studio is OFFLINE or unreachable on port 1234." -ForegroundColor Red
    Write-Host "  Ensure LM Studio is open and the local server is started (lms server start)." -ForegroundColor DarkYellow
}

# 2. Check Google Gemini Cloud Status
Write-Host "`n[2/4] Checking Google Gemini Cloud..." -ForegroundColor Yellow
$geminiKey = [System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY')
if ([string]::IsNullOrWhiteSpace($geminiKey)) {
    $geminiKey = [System.Environment]::GetEnvironmentVariable('GOOGLE_API_KEY')
}

if ([string]::IsNullOrWhiteSpace($geminiKey)) {
    Write-Host "  [NOTICE] GEMINI_API_KEY is not set." -ForegroundColor Yellow
    Write-Host "  To enable Gemini 3.8 Flash / 3.1 Pro:" -ForegroundColor Gray
    Write-Host "  1. Get a key at https://aistudio.google.com/app/apikey (free)" -ForegroundColor Gray
    Write-Host "  2. Set environment variable: setx GEMINI_API_KEY 'AIzaSy...'" -ForegroundColor Gray
} elseif ($geminiKey.StartsWith("AIzaSy")) {
    Write-Host "  [OK] Valid Google AI Studio API key format detected." -ForegroundColor Green
} else {
    Write-Host "  [WARNING] GEMINI_API_KEY exists but does not match standard AI Studio format ('AIzaSy...')." -ForegroundColor DarkYellow
}

# 3. Check Anthropic Claude Status
Write-Host "`n[3/4] Checking Anthropic Claude Cloud..." -ForegroundColor Yellow
$claudeKey = [System.Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY')
if ([string]::IsNullOrWhiteSpace($claudeKey)) {
    Write-Host "  [NOTICE] ANTHROPIC_API_KEY is not set." -ForegroundColor Gray
    Write-Host "  Whenever you activate your Claude subscription/key, set ANTHROPIC_API_KEY" -ForegroundColor Gray
    Write-Host "  to unlock Claude Opus 5 and Sonnet 5 hot-swapping." -ForegroundColor Gray
} else {
    Write-Host "  [OK] ANTHROPIC_API_KEY detected." -ForegroundColor Green
}

# 4. Check VS Code Roo Code Configuration
Write-Host "`n[4/4] Checking VS Code Roo Code Configuration..." -ForegroundColor Yellow
$roomodes = "c:\AI-Project\.roomodes"
$clinerules = "c:\AI-Project\.clinerules"
$vscodeSettings = "c:\AI-Project\.vscode\settings.json"

if (Test-Path $roomodes) {
    Write-Host "  [OK] .roomodes exists (Orchestrator & Operator modes configured)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] .roomodes missing" -ForegroundColor Red
}

if (Test-Path $clinerules) {
    Write-Host "  [OK] .clinerules exists (Golden rules configured)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] .clinerules missing" -ForegroundColor Red
}

if (Test-Path $vscodeSettings) {
    Write-Host "  [OK] .vscode/settings.json exists" -ForegroundColor Green
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                    AUDIT COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
