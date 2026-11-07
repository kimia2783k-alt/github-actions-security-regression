# Enter project venv from anywhere (handles Persian path encoding)
$proj = Get-ChildItem -Path D:\ -Directory |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'requirements.txt') } |
  Select-Object -First 1
if (-not $proj) {
  Write-Error "Project folder with requirements.txt not found under D:\"
  exit 1
}
Set-Location -LiteralPath $proj.FullName
Write-Host "Project:" $proj.FullName
& .\.venv\Scripts\Activate.ps1
Write-Host "venv active. Next: edit .env then run scripts\try_aidev_download.py"
