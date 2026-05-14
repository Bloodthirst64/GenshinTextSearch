Set-Location $PSScriptRoot

Write-Host "========================================"
Write-Host "  Genshin Text Search 一键启动"
Write-Host "========================================"
Write-Host ""

Write-Host "启动后端服务器..."
Set-Location "$PSScriptRoot\server"
conda activate GenshinTextSearch
python server.py
