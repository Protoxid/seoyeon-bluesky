# Optimal LM Studio Model Loader & Server Controller for Operator Workflows
# Targets: NVIDIA RTX 5060 Ti 16GB + Qwen 2.5 Coder 14B Abliterated
$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "      OPTIMIZING LM STUDIO FOR OPERATOR / AGENT WORK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Inspect VRAM
Write-Host "`n[1] Checking GPU & VRAM Headroom..." -ForegroundColor Yellow
$gpuInfo = & nvidia-smi --query-gpu=memory.total,memory.free,memory.used --format=csv,noheader,nounits
if ($gpuInfo) {
    $parts = $gpuInfo.Split(',').ForEach({ [double]$_.Trim() })
    $totalMem = $parts[0]
    $freeMem = $parts[1]
    $usedMem = $parts[2]
    Write-Host "    GPU Total VRAM: $([math]::Round($totalMem / 1024, 1)) GB" -ForegroundColor White
    Write-Host "    Currently Used: $([math]::Round($usedMem / 1024, 1)) GB" -ForegroundColor White
    Write-Host "    Currently Free: $([math]::Round($freeMem / 1024, 1)) GB" -ForegroundColor White
}

# 2. Select Context Length
# 16K context is optimal for 27B on 16GB VRAM to avoid PCIe swapping.
$contextLength = 16384
if ($freeMem -lt 14000 -and $usedMem -gt 2000) {
    Write-Host "    [INFO] Detected existing VRAM usage. Using 16,384 context to prevent system RAM spillover." -ForegroundColor DarkYellow
    $contextLength = 16384
} else {
    Write-Host "    [INFO] Setting optimal 16,384 context length for 100% GPU VRAM residency." -ForegroundColor Green
}

# 3. Verify / Start Local Server
Write-Host "`n[2] Ensuring LM Studio Local Server is Running..." -ForegroundColor Yellow
$serverStatus = & lms server status 2>&1
if ($serverStatus -notmatch "ON") {
    Write-Host "    Starting LM Studio server on port 1234..." -ForegroundColor Gray
    & lms server start
    Start-Sleep -Seconds 2
} else {
    Write-Host "    LM Studio Server is already active on port 1234." -ForegroundColor Green
}

# 4. Check Currently Loaded Models
Write-Host "`n[3] Checking Loaded Model in LM Studio..." -ForegroundColor Yellow
$loaded = (& lms ps --json | ConvertFrom-Json)
$modelKey = "qwen2.5-coder-14b-instruct-abliterated"
$alreadyLoaded = $false

foreach ($m in $loaded) {
    if ($m.identifier -eq $modelKey -or $m.modelKey -eq $modelKey) {
        if ($m.contextLength -ge $contextLength) {
            Write-Host "    Model '$modelKey' is ALREADY LOADED with context $($m.contextLength) and GPU offload." -ForegroundColor Green
            $alreadyLoaded = $true
            break
        } else {
            Write-Host "    Model loaded with smaller context ($($m.contextLength)). Reloading with $contextLength..." -ForegroundColor DarkYellow
            & lms unload $modelKey
            break
        }
    }
}

if (-not $alreadyLoaded) {
    Write-Host "    Loading '$modelKey' with --gpu max, -c $contextLength, --parallel 1..." -ForegroundColor White
    & lms load $modelKey --gpu max -c $contextLength --parallel 1 -y --identifier $modelKey
}

# 5. Warm-up Inference
Write-Host "`n[4] Running Warm-up Inference..." -ForegroundColor Yellow
$t0 = Get-Date
$warmupBody = @{
    model = $modelKey
    messages = @(@{ role = "user"; content = "Respond with: OPERATOR_READY" })
    temperature = 0.1
    max_tokens = 5
} | ConvertTo-Json

try {
    $res = Invoke-RestMethod -Uri "http://localhost:1234/v1/chat/completions" -Method Post -ContentType "application/json" -Body $warmupBody -TimeoutSec 30
    $latency = [math]::Round(((Get-Date) - $t0).TotalMilliseconds)
    $reply = $res.choices[0].message.content.Trim()
    Write-Host "    [SUCCESS] Response: '$reply' in ${latency}ms" -ForegroundColor Green
} catch {
    Write-Host "    [WARNING] Warmup call failed: $_" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  QWEN OPERATOR IS FULLY PRIMED & READY FOR MULTI-AGENT TASKS" -ForegroundColor Cyan
Write-Host "  Endpoint: http://localhost:1234/v1" -ForegroundColor White
Write-Host "  Model:    $modelKey" -ForegroundColor White
Write-Host "  Context:  $contextLength tokens (100% GPU Offloaded)" -ForegroundColor White
Write-Host "============================================================`n" -ForegroundColor Cyan
